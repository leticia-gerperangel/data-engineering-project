# Schemas for the taxi data, including data types and date parsing information.
# Used in both the ingestion script and the web_to_gcp script to ensure consistent data handling.

DTYPE_YELLOW = {
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

DTYPE_GREEN = {
    "VendorID": "Int64",
    "passenger_count": "Int64",
    "trip_distance": "float64",
    "RatecodeID": "Int64",
    "store_and_fwd_flag": "string",
    "PULocationID": "Int64",
    "DOLocationID": "Int64",
    "payment_type": "Int64",
    "trip_type": "Int64",
    "fare_amount": "float64",
    "extra": "float64",
    "mta_tax": "float64",
    "tip_amount": "float64",
    "tolls_amount": "float64",
    "improvement_surcharge": "float64",
    "total_amount": "float64",
    "congestion_surcharge": "float64",
    "ehail_fee": "float64"
    }

PARSE_DATES = {
    "yellow": ["tpep_pickup_datetime", "tpep_dropoff_datetime"],
    "green": ["lpep_pickup_datetime", "lpep_dropoff_datetime"]
}

DTYPES = {
    "yellow": {"dtype": DTYPE_YELLOW, "parse_dates": PARSE_DATES["yellow"]}, 
    "green": {"dtype": DTYPE_GREEN, "parse_dates": PARSE_DATES["green"]} 
}
