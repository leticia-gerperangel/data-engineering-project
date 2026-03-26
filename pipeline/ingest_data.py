#!/usr/bin/env python
# coding: utf-8


import pandas as pd
from sqlalchemy import create_engine

# Parameters for data ingestion
year = 2021
month = 1

# Postgres connection parameters
pg_user = 'root'
pg_password = 'root'
pg_host = 'localhost'
pg_port = '5433'
pg_db = 'ny_taxi'


prefix = 'https://github.com/DataTalksClub/nyc-tlc-data/releases/download/yellow/'
url = f'{prefix}/yellow_tripdata_{year}-{month:02d}.csv.gz'

df = pd.read_csv(url)

df.head()

len(df)

df.dtypes

dtype = {
    "VendorID": "Int64",
    "passenger_count": "Int64",
    "trip_distance": "float64",
    "RatecodeID": "Int64",
    "store_and_fwd_flag": "string",
    "PULocationID": "Int64",
    "DOLocationID": "Int64",
    "payment_type": "Int64",
    "fare_amount": "float64",
    "extra": "float64",
    "mta_tax": "float64",
    "tip_amount": "float64",
    "tolls_amount": "float64",
    "improvement_surcharge": "float64",
    "total_amount": "float64",
    "congestion_surcharge": "float64"
}

parse_dates = [
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime"
]

df = pd.read_csv(
    prefix + 'yellow_tripdata_2021-01.csv.gz',
    nrows=100,
    dtype=dtype,
    parse_dates=parse_dates
)

df.head()


# Create database connection
engine = create_engine(f'postgresql+psycopg://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db}')


# Get DDL schema
print(pd.io.sql.get_schema(df, name='yellow_taxi_data', con=engine))


# Ingest data in chuks
df_iter = pd.read_csv(
    url,
    dtype=dtype,
    parse_dates=parse_dates,
    iterator=True,
    chunksize=100000
)


# Iterate over chunks to insert data
for df_chunk in df_iter:
    df_chunk.to_sql(name='yellow_taxi_data', con=engine, if_exists='append')
    print(len(df_chunk))

