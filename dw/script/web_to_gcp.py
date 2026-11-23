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

from ingestion.schemas import DTYPES

"""
Downloads NYC TLC data from GitHub, converts it to Parquet, and uploads to Google Cloud Storage.
For CSV files, it downloads the .csv.gz, converts to Parquet, and uploads both (if --upload-csv).
Environment variables (via .env or system):
    - GCP_GCS_BUCKET: name of the target GCS bucket
    - GOOGLE_APPLICATION_CREDENTIALS: path to GCP service account JSON key file
"""

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def build_url(service: str, year: int, month: int) -> str:
    BASE_URL = "https://github.com/DataTalksClub/nyc-tlc-data/releases/download/"
    return f"{BASE_URL}{service}/{service}_tripdata_{year}-{month:02d}.csv.gz"

def load_env_vars():
    """Load environment variables from .env file if it exists, otherwise rely on system environment variables."""
    current = Path(__file__).resolve().parent
    env_loaded = False
    for candidate in [current, *current.parents]:
        for env_file in (candidate / ".env_encoded", candidate / "containers" / ".env_encoded"):
            if env_file.exists():
                load_dotenv(env_file)
                logger.info(f"Environment loaded from: {env_file}")
                env_loaded = True
                break
        if env_loaded:
            break
    if not env_loaded:
        logger.warning("Not found .env — using system environment variables")
    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        credentials_path = os.getenv("GCP_APPLICATION_CREDENTIALS")
        if credentials_path:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path


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
    """Download a file, returning False only when the source returns HTTP 404."""
    logger.info(f"Downloading: {url}")
    try:
        with requests.get(url, timeout=timeout, stream=True) as response:
            if response.status_code == 404:
                logger.warning(f"File not found (404): {url}")
                return False
            response.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        logger.info(f"Downloaded: {dest.name} ({dest.stat().st_size / 1_048_576:.1f} MB)")
        return True
    except requests.exceptions.RequestException as exc:
        logger.error(f"Error downloading: {exc}")
        raise

def csv_gz_to_parquet(csv_gz_path: Path, service: str) -> Path:
    """Decompress a .csv.gz file to .csv, convert it to Parquet, and return the Parquet file path."""

    csv_path = csv_gz_path.with_suffix("")  # remove .gz extension for the intermediate CSV file
    parquet_path = csv_path.with_suffix(".parquet")
 
    try:
        logger.info(f"Decompressing: {csv_gz_path.name}")
        with gzip.open(csv_gz_path, "rb") as f_in, open(csv_path, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)

        logger.info(f"Converting to Parquet: {csv_path.name}")
        schema = DTYPES[service]
        df = pd.read_csv(
            csv_path,
            dtype=schema["dtype"],
            parse_dates=schema["parse_dates"],
        )
        df.to_parquet(parquet_path, engine="pyarrow", index=False)
        logger.info(f"Parquet generated: {parquet_path.name} ({len(df):,} rows)")
        return parquet_path
    except Exception:
        parquet_path.unlink(missing_ok=True)
        raise
    finally:
        csv_path.unlink(missing_ok=True)


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
    Download one month's CSV archive, convert it to Parquet, and upload the output.
    Optionally upload the original compressed CSV archive as well.
    Returns False only when the source file returns HTTP 404.
    """
    if not 1 <= month <= 12:
        raise ValueError(f"Month must be between 1 and 12; got {month}.")

    url = build_url(service, year, month)
    month_str = f"{month:02d}"
    filename = f"{service}_tripdata_{year}-{month_str}"
 
    local_file = tmp_dir / f"{filename}.csv.gz"
    parquet_path = tmp_dir / f"{filename}.parquet"
    try:
        if not download_file(url, local_file):
            return False

        parquet_path = csv_gz_to_parquet(local_file, service)
        if upload_csv:
            upload_to_gcs(bucket, f"{service}/csv/{filename}.csv.gz", local_file)
        upload_to_gcs(bucket, f"{service}/{filename}.parquet", parquet_path)
        return True
    finally:
        local_file.unlink(missing_ok=True)
        parquet_path.unlink(missing_ok=True)


def parse_months(months: tuple[str, ...]) -> range | list[int]:
    if not months or months == ("all",):
        return range(1, 13)

    try:
        month_list = [int(month) for value in months for month in value.split()]
    except ValueError as exc:
        raise click.BadParameter(
            'Use "all" or month numbers from 1 to 12.', param_hint="--months"
        ) from exc

    if not month_list or any(month < 1 or month > 12 for month in month_list):
        raise click.BadParameter(
            'Month numbers must be between 1 and 12.', param_hint="--months"
        )

    return month_list

# ── CLI ───────────────────────────────────────────────────────────────────────
 
@click.command()
@click.option(
    "--service", required=True, type=click.Choice(["yellow", "green"]), help="Type NYC TLC service",
)
@click.option("--year", required=True, type=click.IntRange(min=1), help="Year of data to process")
@click.option(
    "--months", default=["all"], help='Months to process: "all" or space-separated list: 1 2 3', multiple=True,
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

    month_list = parse_months(months)

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