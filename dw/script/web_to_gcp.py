import os
import shutil
import gzip
import logging
from pathlib import Path
import sys
import tempfile

import click
import requests
import pandas as pd
from google.cloud import storage
from dotenv import load_dotenv

from ingestion.schemas import DTYPES, PARSE_DATES

"""
Dowloads NYC TLC data from GitHub, converts it to Parquet, and uploads to Google Cloud Storage.
For CSV files, it downloads the .csv.gz, converts to Parquet, and uploads both (if --upload-csv).
Enviroment variables (via .env or system):
    - GCP_GCS_BUCKET: name of the target GCS bucket
    - GCP_APPLICATION_CREDENTIALS: path to GCP service account JSON key file
"""

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def build_url(service: str, year: int, month: int) -> tuple[str, str]:
    BASE_URL = "https://github.com/DataTalksClub/nyc-tlc-data/releases/download/"
    url = f"{BASE_URL}{service}/{service}_tripdata_{year}-{month:02d}.csv.gz"
    return url, "csv"

def load_env_vars():
    """Load environment variables from .env file if it exists, otherwise rely on system environment variables."""
    current = Path(__file__).resolve().parent
    for candidate in [current, *current.parents]:
        env_file = candidate / ".env_encoded"
        if env_file.exists():
            load_dotenv(env_file)
            logger.info(f".env loaded from: {env_file}")
            return
    logger.warning("Not found .env — using system environment variables")


def clean_local_files(*file_paths):
    """Remove local files after processing."""
    for file_path in file_paths:
        try:
            if Path(file_path).exists():
                Path(file_path).unlink()
                logger.info(f"Deleted: {file_path}")
        except Exception as e:
            logger.error(f"Failed to delete {file_path}: {e}")

def download_file(url: str, dest: Path, timeout: int = 60) -> bool:
    """Download a file from a URL with error handling."""
    logger.info(f"Downloading: {url}")
    try:
        response = requests.get(url, timeout=timeout, stream=True)
        if response.status_code == 404:
            logger.warning(f"File not found (404): {url}")
            return False
        response.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        logger.info(f"Downloaded: {dest.name} ({dest.stat().st_size / 1_048_576:.1f} MB)")
        return True
    except requests.exceptions.RequestException as exc:
        logger.error(f"Error downloading: {exc}")
        return False

def csv_gz_to_parquet(csv_gz_path: Path, service: str) -> Path:
    """Decompress a .csv.gz file to .csv, convert it to Parquet, and return the Parquet file path."""

    csv_path = csv_gz_path.with_suffix("")  # remove .gz extension for the intermediate CSV file
 
    logger.info(f"Decompressing: {csv_gz_path.name}")
    with gzip.open(csv_gz_path, "rb") as f_in, open(csv_path, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)
 
    logger.info(f"Converting to Parquet: {csv_path.name}")
    df = pd.read_csv(
        csv_path,
        dtype=DTYPES[service],
        parse_dates=PARSE_DATES[service],
    )
    parquet_path = csv_path.with_suffix(".parquet")
    df.to_parquet(parquet_path, engine="pyarrow", index=False)
    logger.info(f"Parquet generated: {parquet_path.name} ({len(df):,} rows)")
 
    csv_path.unlink()  # remove intermediate CSV file
    return parquet_path


def upload_to_gcs(bucket: str, object_name: str, local_file: str) -> None:
    """
    Ref: https://cloud.google.com/storage/docs/uploading-objects#storage-upload-object-python
    """
    try:
        client = storage.Client()
        bucket_obj = client.bucket(bucket)
        blob = bucket_obj.blob(object_name)
        blob.upload_from_filename(local_file)
        logger.info(f"Uploaded to GCS: {object_name}")
    except Exception as e:
        logger.error(f"Failed to upload {local_file} to GCS: {e}")
        raise

def process_month(
    service: str,
    year: int,
    month: int,
    bucket: str,
    upload_csv: bool,
    tmp_dir: Path,
) -> bool:
    """
    Process a specific month:
      - CSV: download .csv.gz, convert to Parquet, upload Parquet (and CSV if --upload-csv)
      - Parquet: download and upload directly
    Returns True if successful.
    """
    url, fmt = build_url(service, year, month)
    month_str = f"{month:02d}"
    filename = f"{service}_tripdata_{year}-{month_str}"
 
    if fmt == "csv":
        local_file = tmp_dir / f"{filename}.csv.gz"
        ok = download_file(url, local_file)
        if not ok:
            return False
 
        try:
            # Upload CSV if requested
            if upload_csv:
                upload_to_gcs(bucket, f"{service}/csv/{filename}.csv.gz", local_file)
 
            # Convert and upload Parquet
            parquet_path = csv_gz_to_parquet(local_file, service)
            upload_to_gcs(bucket, f"{service}/{filename}.parquet", parquet_path)
            parquet_path.unlink()
        finally:
            if local_file.exists():
                local_file.unlink()
 
    return True

# ── CLI ───────────────────────────────────────────────────────────────────────
 
@click.command()
@click.option(
    "--service", required=True, type=click.Choice(["yellow", "green"]), help="Type NYC TLC service",
)
@click.option("--year", required=True, type=int, help="Year of data to process")
@click.option(
    "--months", default="all", help='Months to process: "all" or space-separated list: 1 2 3', multiple=True,
)
@click.option(
    "--bucket", default=None, envvar="GCP_GCS_BUCKET", help="Name of the GCS bucket (or environment variable GCP_GCS_BUCKET)",
)
@click.option(
    "--upload-csv", is_flag=True, default=False, help="If set, also uploads the original CSV.gz file to GCS",
)

def main(service, year, months, bucket, upload_csv):
    load_env_vars()

    if not bucket:
        bucket = os.getenv("GCP_GCS_BUCKET")
    if not bucket:
        logger.error("GCS bucket name must be provided via --bucket or GCP_GCS_BUCKET environment variable")
        sys.exit(1)

    if not months or months == ("all",) or list(months) == ["all"]:
        month_list = range(1, 13)
    else:
        # Parse space-separated month list from command line
        month_list = [int(m) for tocken in months for m in tocken.split()]

    logger.info(f"Service: {service} | Year: {year} | Months: {month_list}")
    logger.info(f"Bucket  : gs://{bucket}/{service}/")

    results = {"ok": [], "skip": [], "error": []}

    with tempfile.TemporaryDirectory(prefix="nyc_tlc_") as tmp_str:
        tmp_dir = Path(tmp_str)
        for month in month_list:
            try:
                ok = process_month(service, year, month, bucket, upload_csv, tmp_dir)
                if ok:
                    results["ok"].append(month)
                else:
                    results["skip"].append(month)
            except Exception as exc:
                logger.error(f"Error in month {month:02d}/{year}: {exc}", exc_info=True)
                results["error"].append(month)
    # Summary
    logger.info("─" * 50)
    logger.info(f"Completed : {results['ok']}")
    if results["skip"]:
        logger.warning(f"Not found (404): {results['skip']}")
    if results["error"]:
        logger.error(f"Errors : {results['error']}")
        sys.exit(1)
    logger.info("ETL completed.")


if __name__ == "__main__":
    main()