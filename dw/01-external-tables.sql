-- BigQuery Data Warehouse Setup — NYC Taxi Trip Data

-- Creating EXTERNAL TABLE referring to gcs path
CREATE OR REPLACE EXTERNAL TABLE `nytaxi.external_yellow_tripdata`
OPTIONS (
  format = 'CSV',
  uris = ['gs://data-engineering-demo/yellow/yellow_tripdata_2019-*.csv', 'gs://data-engineering-demo/yellow/yellow_tripdata_2020-*.csv']
);

CREATE OR REPLACE EXTERNAL TABLE `nytaxi.external_green_tripdata`
OPTIONS (
  format = 'CSV',
  uris = ['gs://data-engineering-demo/green/green_tripdata_2019-*.csv', 'gs://data-engineering-demo/green/green_tripdata_2020-*.csv']
);

-- Quick check yellow and green trip data
SELECT * FROM nytaxi.external_yellow_tripdata limit 10;

SELECT * FROM nytaxi.external_green_tripdata limit 10;
