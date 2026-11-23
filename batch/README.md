# Batch Processing with Apache Spark

Apache Spark is a tool for processing large datasets. PySpark lets us use Spark with Python.

In this project, PySpark runs Spark locally in WSL to process the 2020 Yellow and Green taxi data. The notebooks combine both datasets, standardize their columns, remove invalid trips, save the results as Parquet files, and use Spark SQL to analyze trip counts, distance, revenue, and duration.


## Notebooks

| Notebook | Purpose |
|---|---|
| [`taxi_trip/taxi_schema.ipynb`](notebook/taxi_trip/taxi_schema.ipynb) | Downloads 2020 monthly Parquet files, standardizes both taxi types and writes cleaned data to `taxi_trip/data/taxi_2020_clean/`. |
| [`sparkSQL.ipynb`](notebook/sparkSQL.ipynb) | Reads the cleaned data and calculates trips, average distance, revenue and trip duration with Spark SQL. |
| [`spark-gcs.ipynb`](notebook/spark-gcs.ipynb) | Demonstrates reading Parquet data from GCS using a service-account key and the GCS Hadoop connector. |
| [`test/test.ipynb`](notebook/test/test.ipynb) | Verifies the local Spark setup by reading a CSV and writing a Parquet file. |


```bash
cd batch
uv sync
uv run python -m jupyter notebook
```

>[!Note]
>This project uses Java 17 and Apache Spark 4.x in WSL. The local Java environment avoids conflicts with Java versions installed on Windows.

