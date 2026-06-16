#!/usr/bin/env python
# coding: utf-8

import sys
import pandas as pd
from sqlalchemy import create_engine, text
import click
from schemas import DTYPES
from dotenv import load_dotenv
from pathlib import Path

# Load .env from containers/ folder
load_dotenv(Path(__file__).parent.parent / "containers" / ".env_postgres") 


def build_url(taxi_type: str, year: int, month: int) -> tuple[str, str]:
    """
    Build the URL for the taxi data based on the taxi type, year, and month.
    """
    prefix = 'https://github.com/DataTalksClub/nyc-tlc-data/releases/download'
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
# This allows to specify database connection parameters, target table name, and data year/month when running the script.
@click.command()
@click.option('--pg-user', envvar='POSTGRES_USER', help='PostgreSQL user')
@click.option('--pg-pass', envvar='POSTGRES_PASSWORD', help='PostgreSQL password')
@click.option('--pg-host', envvar='POSTGRES_HOST', help='PostgreSQL host')
@click.option('--pg-port', envvar='POSTGRES_PORT', type=int, help='PostgreSQL port')
@click.option('--pg-db', envvar='POSTGRES_DB', help='PostgreSQL database name')
@click.option('--target-table', default='yellow_taxi_data', help='Target table name')
@click.option('--year', default=2021, type=int, help='Year of data')
@click.option('--month', default=1, type=int, help='Month of data')
@click.option('--taxi-type', default='yellow', type=click.Choice(['yellow', 'green']), help='Type of taxi (yellow or green)')
@click.option('--chunk-size', default=100000, type=int, help='Chunk size for reading data')

def run(taxi_type, year, month, pg_user, pg_pass, pg_host, pg_port, pg_db, target_table, chunk_size):

    # Name of the target table in the database. If not provided, it defaults to "{taxi_type}_tripdata".
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

    # Ingest data in chunks
    first_chunk = True
    total_rows = 0

    try:
        for i, df_chunk in enumerate(read_chunks(url, taxi_type, chunk_size), start=1):
            actual_chunk_size = len(df_chunk)
            total_rows += actual_chunk_size

            df_chunk.to_sql(
            name=table,
            con=engine,
            if_exists='append',   # creates if not exists, appends if exists
            index=False,
            chunksize=chunk_size
        )

            print(f"Chunk {i}: {actual_chunk_size:,} rows inserted")

        print(f"\n Ingestion completed! Total rows inserted: {total_rows:,}")

    except Exception as e:
        print(f"\nERROR during ingestion: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        engine.dispose()  # Close the database connection


if __name__ == '__main__':
    run()