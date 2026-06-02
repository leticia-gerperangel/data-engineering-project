## Project Structure

- `models/`
  - `staging/` — Clean raw BigQuery tables (views).
  - `intermediate/` — Union of yellow and green taxi data (views).
  - `marts/` — Star schema: dimensions, fact table, and aggregations (tables).

- `seeds/` — Static lookup tables, such as taxi zones and payment types.
- `macros/` — Reusable SQL functions.
- `analyses/` — Ad-hoc queries; compile with `dbt compile` and run in BigQuery.
- `tests/` — Singular data quality tests.