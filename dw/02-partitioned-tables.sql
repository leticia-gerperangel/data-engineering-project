-- Create a PARTIONED TABLE (by pickup date) from external table
CREATE OR REPLACE TABLE nytaxi.yellow_tripdata_partitioned
PARTITION BY
  DATE(tpep_pickup_datetime) AS
SELECT * FROM nytaxi.external_yellow_tripdata;

-- Create a PARTIONED TABLE (by pickup date) from external table
CREATE OR REPLACE TABLE nytaxi.green_tripdata_partitioned
PARTITION BY
  DATE(lpep_pickup_datetime) AS
SELECT * FROM nytaxi.external_green_tripdata;


-- PARTITION IMPACT
-- Shows the performance difference between partitioned and non-partitioned tables. 
-- Run each query and check bytes processed in the BigQuery UI to verify the impact.


-- Non-partitioned (from external table) reference table for comparison
CREATE OR REPLACE TABLE nytaxi.yellow_tripdata_non_partitioned AS
SELECT * FROM nytaxi.external_yellow_tripdata;


-- Scans only June 2019 partition 
SELECT DISTINCT(VendorID)
FROM nytaxi.yellow_tripdata_non_partitioned
WHERE DATE(tpep_pickup_datetime) BETWEEN '2019-06-01' AND '2019-06-30';

SELECT DISTINCT(VendorID)
FROM nytaxi.yellow_tripdata_partitioned
WHERE DATE(tpep_pickup_datetime) BETWEEN '2019-06-01' AND '2019-06-30';

-- Inspect partitions metadata
SELECT table_name, partition_id, total_rows, total_logical_bytes
FROM `nytaxi.INFORMATION_SCHEMA.PARTITIONS`
WHERE table_name = 'yellow_tripdata_partitioned'
ORDER BY total_rows DESC;