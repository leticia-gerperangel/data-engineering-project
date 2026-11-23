import gzip
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import click
import pandas as pd
import requests
from click.testing import CliRunner

from dw.script.web_to_gcp import (
    csv_gz_to_parquet,
    download_file,
    load_env_vars,
    main,
    parse_months,
    process_month,
)


# Minimal records cover the different pickup/dropoff column names for each service.
YELLOW_CSV = (
    "VendorID,tpep_pickup_datetime,tpep_dropoff_datetime,passenger_count,trip_distance\n"
    "1,2020-01-01 10:00:00,2020-01-01 10:10:00,2,1.5\n"
)
GREEN_CSV = (
    "VendorID,lpep_pickup_datetime,lpep_dropoff_datetime,passenger_count,trip_distance,trip_type\n"
    "2,2020-01-01 10:00:00,2020-01-01 10:10:00,1,1.2,1\n"
)


def write_gzip_csv(path: Path) -> None:
    with gzip.open(path, "wt", encoding="utf-8") as file:
        file.write(YELLOW_CSV)


def write_green_gzip_csv(path: Path) -> None:
    with gzip.open(path, "wt", encoding="utf-8") as file:
        file.write(GREEN_CSV)


class WebToGcpTests(unittest.TestCase):
    def test_csv_gz_to_parquet_applies_schema(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_gz_path = Path(temp_dir) / "yellow_tripdata_2020-01.csv.gz"
            write_gzip_csv(csv_gz_path)

            parquet_path = csv_gz_to_parquet(csv_gz_path, "yellow")
            result = pd.read_parquet(parquet_path)

            self.assertEqual(len(result), 1)
            self.assertEqual(str(result["VendorID"].dtype), "Int64")
            self.assertTrue(pd.api.types.is_datetime64_any_dtype(result["tpep_pickup_datetime"]))
            self.assertEqual(result.loc[0, "trip_distance"], 1.5)
            self.assertFalse(csv_gz_path.with_suffix("").exists())

    def test_csv_gz_to_parquet_applies_green_schema(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_gz_path = Path(temp_dir) / "green_tripdata_2020-01.csv.gz"
            write_green_gzip_csv(csv_gz_path)

            parquet_path = csv_gz_to_parquet(csv_gz_path, "green")
            result = pd.read_parquet(parquet_path)

            self.assertEqual(len(result), 1)
            self.assertEqual(str(result["VendorID"].dtype), "Int64")
            self.assertTrue(pd.api.types.is_datetime64_any_dtype(result["lpep_pickup_datetime"]))
            self.assertEqual(result.loc[0, "trip_type"], 1)

    @patch("dw.script.web_to_gcp.upload_to_gcs")
    @patch("dw.script.web_to_gcp.download_file")
    def test_process_month_uploads_parquet_and_optional_csv(self, download, upload):
        # Replace network and GCS I/O while still exercising conversion and object naming.
        def create_download(_url, destination):
            write_gzip_csv(destination)
            return True

        download.side_effect = create_download
        with tempfile.TemporaryDirectory() as temp_dir:
            result = process_month("yellow", 2020, 1, "test-bucket", True, Path(temp_dir))

            self.assertTrue(result)
            self.assertEqual(
                [call.args[1] for call in upload.call_args_list],
                [
                    "yellow/csv/yellow_tripdata_2020-01.csv.gz",
                    "yellow/yellow_tripdata_2020-01.parquet",
                ],
            )
            self.assertEqual(list(Path(temp_dir).iterdir()), [])

    @patch("dw.script.web_to_gcp.upload_to_gcs")
    @patch("dw.script.web_to_gcp.download_file", return_value=False)
    def test_process_month_skips_missing_source(self, download, upload):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = process_month("yellow", 2020, 1, "test-bucket", False, Path(temp_dir))

        self.assertFalse(result)
        upload.assert_not_called()

    def test_download_file_raises_network_errors(self):
        with patch(
            "dw.script.web_to_gcp.requests.get",
            side_effect=requests.exceptions.ConnectionError("offline"),
        ):
            with self.assertRaises(requests.exceptions.ConnectionError):
                download_file("https://example.test/data.csv.gz", Path("unused"))

    def test_download_file_returns_false_for_404(self):
        response = MagicMock()
        response.__enter__.return_value = response
        response.status_code = 404
        with patch("dw.script.web_to_gcp.requests.get", return_value=response):
            self.assertFalse(download_file("https://example.test/missing.csv.gz", Path("unused")))

    def test_month_parser_checks_range_and_default(self):
        self.assertEqual(list(parse_months(("all",))), list(range(1, 13)))
        self.assertEqual(parse_months(("1 2",)), [1, 2])
        with self.assertRaises(click.BadParameter):
            parse_months(("13",))

    @patch("dw.script.web_to_gcp.load_dotenv")
    @patch.object(Path, "exists", return_value=False)
    def test_legacy_credentials_variable_is_mapped(self, _exists, _load_dotenv):
        # Isolate this check from the real environment file and other credentials.
        with patch.dict(os.environ, {"GCP_APPLICATION_CREDENTIALS": "service-account.json"}, clear=True):
            load_env_vars()

            self.assertEqual(
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"],
                "service-account.json",
            )

    @patch("dw.script.web_to_gcp.load_env_vars")
    @patch("dw.script.web_to_gcp.process_month", return_value=False)
    def test_cli_defaults_to_all_months(self, process_month_mock, _load_env_vars):
        # Avoid downloads while checking that the CLI schedules all twelve months.
        result = CliRunner().invoke(
            main,
            ["--service", "yellow", "--year", "2020", "--bucket", "test-bucket"],
        )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(
            [call.args[2] for call in process_month_mock.call_args_list],
            list(range(1, 13)),
        )


if __name__ == "__main__":
    unittest.main()
