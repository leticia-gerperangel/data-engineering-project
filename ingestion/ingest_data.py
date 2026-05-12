#!/usr/bin/env python
# coding: utf-8

import sys
import pandas as pd
from sqlalchemy import create_engine, text
import click
from schemas import DTYPES


def build_url(taxi_type: str, year: int, month: int) -> tuple[str, str]:
    """
    Build the URL for the taxi data based on the taxi type, year, and month.
    """
    prefix = 'https://github.com/DataTalksClub/nyc-tlc-data/releases/download/'
    url = f'{prefix}/{taxi_type}/{taxi_type}_tripdata_{year}-{month:02d}.csv.gz'
    return url, "csv"


def read_chunks(url: str, taxi_type: str, chunk_size: int):
    """
    Read the data in chunks and yield each chunk as a DataFrame.
    """
    dtype = DTYPES[taxi_type]["dtype"]
    parse_dates = DTYPES[taxi_type]["parse_dates"]

    # Use pandas to read the CSV file in chunks and yield each chunk as a DataFrame
    yield from pd.read_csv(
        url,
        dtype=dtype,
        parse_dates=parse_dates,
        iterator=True,
        chunksize=chunk_size
    )

def test_connection(engine):
    """
    Test the database connection before starting the ingestion process.
    """
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))


# Command-line argument parsing with click. 
# This allows us to specify database connection parameters, target table name, and data year/month when running the script.
@click.command()
@click.option('--pg-user', default='root', help='PostgreSQL user')
@click.option('--pg-pass', default='root', help='PostgreSQL password')
@click.option('--pg-host', default='localhost', help='PostgreSQL host')
@click.option('--pg-port', default=5433, type=int, help='PostgreSQL port')
@click.option('--pg-db', default='ny_taxi', help='PostgreSQL database name')
@click.option('--target-table', default='yellow_taxi_data', help='Target table name')
@click.option('--year', default=2021, type=int, help='Year of data')
@click.option('--month', default=1, type=int, help='Month of data')
@click.option('--taxi-type', default='yellow', type=click.Choice(['yellow', 'green']), help='Type of taxi (yellow or green)')

def run(taxi_type, year, month, pg_user, pg_pass, pg_host, pg_port, pg_db, target_table):

    # Nombre de tabla automático si no se especifica
    table = target_table or f"{taxi_type}_tripdata"

    # Build the URL for the specified taxi type, year, and month
    url, file_format = build_url(taxi_type, year, month)
    print(f"URL: {url}")

    # Create database connection
    engine = create_engine(f'postgresql+psycopg://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}')

    try:
        test_connection(engine)
        print("PostgreSQL connection: OK")
    except Exception as exc:
        print(f"ERROR: PostgreSQL connection failed: {exc}")
        sys.exit(1)

    # Ingest data in chuks
    first_chunk = True
    total_rows = 0

    for i, df_chunk in enumerate(read_chunks(url, taxi_type, chunk_size), start=1):
        chunk_size = len(df_chunk)
        total_rows += chunk_size

        if first_chunk:
            # First chunk: create table and insert data
            print(f"Creating table '{table}' with the first chunk...")
            df_chunk.to_sql(
                name=table,
                con=engine,
                if_exists='replace',
                index=False,
                chunksize=100000
            )
            first_chunk = False
        else:
            # Subsequent chunks: append data to the existing table
            df_chunk.to_sql(
                name=table,
                con=engine,
                if_exists='append',
                index=False,
                chunksize=100000
            )

        print(f"Chunk {i}: {chunk_size:,} rows inserted")

    print(f"\n Ingestion completed! Total rows inserted: {total_rows:,}")

    engine.dispose()  # Close the database connection


if __name__ == '__main__':
    run()