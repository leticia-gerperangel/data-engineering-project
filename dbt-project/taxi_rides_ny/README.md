## dbt project structure

- `analyses/` — Ad-hoc queries; compile with `dbt compile` and run in BigQuery.
- `macros/` — Reusable SQL functions.
- `models/`
  - `staging/` — Clean raw BigQuery tables (views).
  - `intermediate/` — Union of yellow and green taxi data (views).
  - `marts/` — Star schema: dimensions, fact table, and aggregations (tables).

- `seeds/` — Static lookup tables, such as taxi zones and payment types.
- `tests/` — Singular data quality tests.

- `dbt_proyect.yml` -  dbt looks for this file first. It contains the project name, profile name, default materializations and variables.