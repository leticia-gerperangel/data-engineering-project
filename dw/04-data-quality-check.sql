-- Year distribution — should only contain 2019 and 2020
SELECT
    EXTRACT(YEAR FROM tpep_pickup_datetime) AS year,
    COUNT(*) AS trips
FROM `nytaxi.external_yellow_tripdata`
GROUP BY 1
ORDER BY 1;

-- Null check on critical columns
SELECT
    COUNTIF(VendorID IS NULL)            AS null_vendor,
    COUNTIF(tpep_pickup_datetime IS NULL) AS null_pickup,
    COUNTIF(PULocationID IS NULL)        AS null_pickup_location,
    COUNTIF(total_amount IS NULL)        AS null_total_amount
FROM `nytaxi.external_yellow_tripdata`;

-- Negative values check
SELECT
    COUNTIF(fare_amount < 0)   AS negative_fare,
    COUNTIF(total_amount < 0)  AS negative_total,
    COUNTIF(trip_distance <= 0) AS zero_or_negative_distance,
    COUNTIF(passenger_count <= 0) as zero_passengers,
FROM `nytaxi.external_yellow_tripdata`;
