#!/usr/bin/env python
# coding: utf-8

import pyspark
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .master("local[*]") \
    .appName('taxi_yellow_green') \
    .getOrCreate()


base_url = "https://d37ci6vzurychx.cloudfront.net/trip-data"

months = [f"{m:02d}" for m in range(1, 13)]

year = "2020"

yellow_urls = [f"{base_url}/yellow_tripdata_{year}-{m}.parquet" for m in months]

green_urls  = [f"{base_url}/green_tripdata_{year}-{m}.parquet"  for m in months]


from pyspark.sql import functions as F
from pyspark.sql import types as T

import tempfile
import requests


def download_to_temp(url: str) -> str:
    """
    Downloads a Parquet file from HTTPS to a local temporary file.
    Returns the local path for Spark to read it.
    """
    response = requests.get(url)
    response.raise_for_status()

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".parquet")
    tmp.write(response.content)
    tmp.close()

    return tmp.name

green_schema = T.StructType([
    T.StructField("VendorID", T.LongType(), True),
    T.StructField("lpep_pickup_datetime", T.TimestampType(), True),
    T.StructField("lpep_dropoff_datetime", T.TimestampType(), True),
    T.StructField("store_and_fwd_flag", T.StringType(), True),
    T.StructField("RatecodeID", T.DoubleType(), True),
    T.StructField("PULocationID", T.LongType(), True),
    T.StructField("DOLocationID", T.LongType(), True),
    T.StructField("passenger_count", T.DoubleType(), True),
    T.StructField("trip_distance", T.DoubleType(), True),
    T.StructField("fare_amount", T.DoubleType(), True),
    T.StructField("extra", T.DoubleType(), True),
    T.StructField("mta_tax", T.DoubleType(), True),
    T.StructField("tip_amount", T.DoubleType(), True),
    T.StructField("tolls_amount", T.DoubleType(), True),
    T.StructField("ehail_fee", T.NullType(), True),
    T.StructField("improvement_surcharge", T.DoubleType(), True),
    T.StructField("total_amount", T.DoubleType(), True),
    T.StructField("payment_type", T.DoubleType(), True),
    T.StructField("trip_type", T.DoubleType(), True),
    T.StructField("congestion_surcharge", T.DoubleType(), True)
])

yellow_schema = T.StructType([
    T.StructField("VendorID", T.LongType(), True),
    T.StructField("tpep_pickup_datetime", T.TimestampType(), True),
    T.StructField("tpep_dropoff_datetime", T.TimestampType(), True),
    T.StructField("passenger_count", T.DoubleType(), True),
    T.StructField("trip_distance", T.DoubleType(), True),
    T.StructField("RatecodeID", T.DoubleType(), True),
    T.StructField("store_and_fwd_flag", T.StringType(), True),
    T.StructField("PULocationID", T.LongType(), True),
    T.StructField("DOLocationID", T.LongType(), True),
    T.StructField("payment_type", T.LongType(), True),
    T.StructField("fare_amount", T.DoubleType(), True),
    T.StructField("extra", T.DoubleType(), True),
    T.StructField("mta_tax", T.DoubleType(), True),
    T.StructField("tip_amount", T.DoubleType(), True),
    T.StructField("tolls_amount", T.DoubleType(), True),
    T.StructField("improvement_surcharge", T.DoubleType(), True),
    T.StructField("total_amount", T.DoubleType(), True),
    T.StructField("congestion_surcharge", T.DoubleType(), True),
    T.StructField("airport_fee", T.NullType(), True)
])

def process_month(url: str, service: str):
    """
    Download a month, standardize it, clean it and add year/month partitions.
    Repartition in 4 for efficient writing.
    """
    # 1. Download a temporary local file and read it with the appropriate schema
    local_path = download_to_temp(url)
    df_raw = spark.read.parquet(local_path)
    df_raw.printSchema()

    # 2.  Standardize columns according to taxi type
    if service == "green":
        df = spark.read.schema(green_schema).parquet(local_path)
        df = df.select(
            F.col("VendorID").alias("vendor_id"),
            F.col("lpep_pickup_datetime").alias("pickup_datetime"),
            F.col("lpep_dropoff_datetime").alias("dropoff_datetime"),
            F.col("RatecodeID").alias("ratecode_id"),
            "passenger_count",
            "trip_distance",
            "PULocationID",
            "DOLocationID",
            "fare_amount",
            "total_amount",
            "payment_type"
        )
    elif service == "yellow":
        df = spark.read.schema(yellow_schema).parquet(local_path)
        df = df.select(
            F.col("VendorID").alias("vendor_id"),
            F.col("tpep_pickup_datetime").alias("pickup_datetime"),
            F.col("tpep_dropoff_datetime").alias("dropoff_datetime"),
            F.col("RatecodeID").alias("ratecode_id"),
            "passenger_count",
            "trip_distance",
            "PULocationID",
            "DOLocationID",
            "fare_amount",
            "total_amount",
            "payment_type"
        )
    else:
        raise ValueError(f"Servicio no reconocido: {service}")

    # 3. Add service_type column
    df = df.withColumn("service_type", F.lit(service))

    # 4. Create year and month columns for filtering
    df = df.withColumn("year", F.year("pickup_datetime"))
    df = df.withColumn("month", F.month("pickup_datetime"))

    # 5. Filter
    df = df.filter(df.year == 2020)
    df = df.filter(df.month.isNotNull())

    #  Normalize data types
    df = df.withColumn("payment_type", F.col("payment_type").cast("int"))
    df = df.withColumn("passenger_count", F.col("passenger_count").cast("int"))
    df = df.withColumn("ratecode_id", F.col("ratecode_id").cast("int"))

    # 6. Basic cleaning
    df = df.filter(F.col("trip_distance") > 0)
    df = df.filter(F.col("fare_amount") >= 0)
    df = df.filter(F.col("passenger_count") > 0)
    df = df.filter(F.col("dropoff_datetime") >= F.col("pickup_datetime"))

    # 7. Repartition each month in 4 partitions for efficient writing
    df = df.repartition(4)

    return df

output_path = "data/taxi_2020_clean"

for url in green_urls:
    print(f"Procesando GREEN: {url}")
    df_month = process_month(url, "green")
    df_month.write \
        .mode("append") \
        .partitionBy("year", "month", "service_type") \
        .parquet(output_path)

for url in yellow_urls:
    print(f"Procesando YELLOW: {url}")
    df_month = process_month(url, "yellow")
    df_month.write \
        .mode("append") \
        .partitionBy("year", "month", "service_type") \
        .parquet(output_path)


df_final = spark.read.parquet(output_path)


df_final.printSchema()


df_final.show(10)
