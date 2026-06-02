## Project Structure

models/
├── staging/       # Clean raw BigQuery tables (views)
├── intermediate/  # Union yellow + green taxi (views)
└── marts/         # Star schema — dimensions + fact + aggregations (tables)
seeds/             # Static lookup tables (taxi zones, payment types)
macros/            # Reusable SQL functions
analyses/          # Ad-hoc queries — compile with dbt compile, run in BigQuery
tests/             # Singular data quality tests