## BigQuery Data Warehouse

BigQuery is the data warehouse engine in GCP. It is a serverless analytical database for storing and querying large volumes of data with SQL.

In this project, BigQuery is used to organize NYC Taxi data loaded from GCS, so it can be analyzed and transformed with dbt.

### SQL scripts

- [`01-external-tables.sql`](01-external-tables.sql) creates Yellow and Green external tables over GCS CSV files.
- [`02-partitioned-tables.sql`](02-partitioned-tables.sql) creates tables partitioned by pickup date.
- [`03-partition-clustering-tables.sql`](03-partition-clustering-tables.sql) compares partitioned and clustered tables.
- [`04-data-quality-check.sql`](04-data-quality-check.sql) checks null values and invalid data.

Run the scripts in order in the BigQuery console.

> [!NOTE]
>[`script/web_to_gcp.py`](script/web_to_gcp.py) downloads monthly NYC TLC data, converts it to Parquet and uploads it to GCS. It is not required when the files are already available in the bucket.
>To run it:
>```bash
>uv run --project ingestion python -m dw.script.web_to_gcp --service yellow --year 2020 --months "1 2 3" --bucket <gcs-bucket>
>```
>Set `GCP_GCS_BUCKET` instead of using `--bucket`, or add `--upload-csv` to upload the compressed CSV source.
>Authenticate with `GOOGLE_APPLICATION_CREDENTIALS` or Application Default Credentials. The script uploads Parquet by default; `--upload-csv` stores the original `.csv.gz` under a separate `csv/` path. `01-external-tables.sql` expects uncompressed CSV files, so these uploads are not direct inputs to its external tables.
