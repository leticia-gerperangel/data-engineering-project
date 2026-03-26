#!/usr/bin/env python
# coding: utf-8

import pandas as pd
from sqlalchemy import create_engine
import click

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

"""
Command-line argument parsing with click. This allows us to specify database connection parameters, target table name, and data year/month when running the script.
"""
@click.command()
@click.option('--pg-user', default='root', help='PostgreSQL user')
@click.option('--pg-pass', default='root', help='PostgreSQL password')
@click.option('--pg-host', default='localhost', help='PostgreSQL host')
@click.option('--pg-port', default=5433, type=int, help='PostgreSQL port')
@click.option('--pg-db', default='ny_taxi', help='PostgreSQL database name')
@click.option('--target-table', default='yellow_taxi_data', help='Target table name')
@click.option('--year', default=2021, type=int, help='Year of data')
@click.option('--month', default=1, type=int, help='Month of data')

def run(pg_user, pg_pass, pg_host, pg_port, pg_db, target_table, year, month):

    # URL for the data
    prefix = 'https://github.com/DataTalksClub/nyc-tlc-data/releases/download/yellow/'
    url = f'{prefix}/yellow_tripdata_{year}-{month:02d}.csv.gz'

    # Read a sample of the data to get the schema and preview
    df = pd.read_csv(
        url,
        nrows=100,
        dtype=dtype,
        parse_dates=parse_dates
    )

    # Create database connection
    engine = create_engine(f'postgresql+psycopg://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}')

    # Ingest data in chuks
    df_iter = pd.read_csv(
        url,
        dtype=dtype,
        parse_dates=parse_dates,
        iterator=True,
        chunksize=100000
    )

    first_chunk = True
    total_rows = 0

    for i, df_chunk in enumerate(df_iter, start=1):
        chunk_size = len(df_chunk)
        total_rows += chunk_size

        if first_chunk:
            # First chunk: create table and insert data
            print(f"Creating table '{target_table}' with the first chunk...")
            df_chunk.to_sql(
                name=target_table,
                con=engine,
                if_exists='replace',
                index=False,
                chunksize=100000
            )
            first_chunk = False
        else:
            # Subsequent chunks: append data to the existing table
            df_chunk.to_sql(
                name=target_table,
                con=engine,
                if_exists='append',
                index=False,
                chunksize=100000
            )

        print(f"Chunk {i}: {chunk_size:,} rows inserted")

    print(f"\n Ingestion completed! Total rows inserted: {total_rows:,}")


if __name__ == '__main__':
    run()