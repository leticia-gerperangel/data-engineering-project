-- CLUSTERING IMPACT
-- Clustering on top of partitioning further reduces bytes scanned when filtering or grouping by the clustered columns.

-- Partitioned + clustered by VendorID
CREATE OR REPLACE TABLE nytaxi.yellow_tripdata_partitioned_clustered
PARTITION BY DATE(tpep_pickup_datetime)
CLUSTER BY VendorID AS
SELECT * FROM nytaxi.external_yellow_tripdata;

-- Partitioned only
SELECT count(*) as trips
FROM nytaxi.yellow_tripdata_partitioned
WHERE DATE(tpep_pickup_datetime) BETWEEN '2019-06-01' AND '2020-12-31'
  AND VendorID=1;

-- Partitioned + clustered
SELECT count(*) as trips
FROM nytaxi.yellow_tripdata_partitioned_clustered
WHERE DATE(tpep_pickup_datetime) BETWEEN '2019-06-01' AND '2020-12-31'
  AND VendorID=1;