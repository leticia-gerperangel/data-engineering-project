# Data engineering project

A full end‑to‑end data pipeline that ingests NYC taxi trip data, stores it in Google Cloud Storage and BigQuery, transforms it with dbt, processes it at scale with Apache Spark and visualizes it in an interactive dashboard.

Built following modules of the [Data Engineering Zoomcamp](https://github.com/DataTalksClub/data-engineering-zoomcamp) by DataTalksClub.

---
## Architecture
 
```
┌─────────────────────────────────────────────────────────────────┐
│                        NYC TLC Trip Data                        │
│              (Yellow & Green taxi, 2019–2020)                   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     INGESTION LAYER                             │
│         Docker · PostgreSQL · Python (uv) · Jupyter             │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATION LAYER                         │
│                     Kestra (Docker)                            │
│           ingest → upload GCS → BigQuery tables                │
└──────────┬──────────────────────────────────────┬──────────────┘
           │                                      │
           ▼                                      ▼
┌─────────────────────┐              ┌────────────────────────────┐
│   DATA WAREHOUSE    │              │     BATCH PROCESSING       │
│  GCS  →  BigQuery   │              │  Apache Spark (WSL local)  │
│  External tables    │              │  PySpark DataFrames        │
│  Partitioned tables │              │  Spark SQL analytics       │
└─────────┬───────────┘              └────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                   ANALYTICS LAYER  (dbt)                        │
│              staging → intermediate → marts                     │
│   dim_vendor · dim_zones · dim_payment_type · dim_rate_code     │
│        fact_trips · mart_monthly_revenue · mart_zone_stats      │
└─────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                   DASHBOARD (Looker Studio)                     │
│   Trip trends · Revenue analysis · Geographic distribution      │
└─────────────────────────────────────────────────────────────────┘
```
---

## Tech Stack
 
| Layer | Technology | Description |
|---|---|---|
| Containerization | Docker + Docker Compose | Runs PostgreSQL, pgAdmin and Kestra as isolated containers |
| Local database | PostgreSQL 18 | Staging database for raw CSV ingestion before cloud upload |
| Orchestration | Kestra | UI-driven workflow engine that automates and chains pipeline steps |
| Cloud storage | Google Cloud Storage (GCS) | Data lake storing raw and processed Parquet files |
| Data warehouse | BigQuery | Serverless analytical database with external and partitioned tables |
| Analytics engineering | dbt (BigQuery adapter) | SQL-based transformation framework that builds the star schema |
| Batch processing | Apache Spark 4.x + PySpark | Distributed processing engine for large-scale data standardization and aggregation |
| Visualization | Looker Studio | Interactive dashboard connected directly to BigQuery marts |
| Package manager | uv (Python) | Fast Python package and virtual environment manager |
| Language | Python 3.13 | Used for ingestion scripts, orchestration tasks and Spark jobs |
 
---

## Configuration

Before running the pipeline, copy the environment template and fill in your values:

```bash
cp containers/.env.example containers/.env
```

Edit `containers/.env` with your values.


Place your GCP service account JSON file in `credentials/` (this folder is excluded from git via `.gitignore`).


## Start the local infrastructure

```bash
cd containers/
docker-compose up -d
```

This starts three services: PostgreSQL, pgAdmin (http://localhost:8085) and Kestra (http://localhost:8080).


## Running the pipeline

### Phase 1 — Ingest raw data into PostgreSQL

Ingest NYC taxi data into PostgreSQL. Two options:

**Option A — Run locally with uv:**
```bash
cd ingestion/
uv sync --dev
uv run python ingest_data.py --taxi-type yellow --year 2019 --month 1
uv run python ingest_data.py --taxi-type green --target-table green_taxi_trips --year 2019 --month 1
```

**Option B — Run containerized with Docker:**
```bash
cd ingestion/
docker build -t taxi_ingest:v001 .
docker run -it --rm --network=containers_default --env-file ..\containers\.env_postgres_docker taxi_ingest:v001 --taxi-type green --target-table green_taxi_trips --year 2019 --month 1
```
Verify the data was loaded correctly by opening pgAdmin at `http://localhost:8085`


### Phase 2 — Orchestrate with Kestra

Open the Kestra UI at `http://localhost:8080` and run the flows in order:

| Step | Flow | Purpose |
|---|---|---|
| 1 | `06-gcp-kv-example` | Register GCP values in the Kestra KV store. Run manually from the UI. |
| 2 | `07-gcp-setup` | Create the GCS bucket and BigQuery dataset |
| 3 | `04-postgres-taxi` | Download CSV → PostgreSQL via staging + MERGE (idempotent) |
| 4 | `08-gcp-taxi` | Extract CSV Data → Upload to GCS → BigQuery external + partitioned tables + MERGE |


### Phase 3 — DW

The `08-gcp-taxi` Kestra flow handles the full BigQuery lifecycle automatically.
For manual setup or ad-hoc queries against the raw data, use the scripts in `dw/`.

- `01-external-tables.sql` Create external tables over CSV files in GCS.
- `02-partitioned-tables.sql` Create production tables partitioned by pickup date.
- `03-partition-clustering.sql` Demonstrate the performance impact of partitioning and clustering.
- `04-data-quality-check.sql` Validate data quality before dbt transformations.

Run them directly in the [BigQuery console](https://console.cloud.google.com/bigquery).


### Phase 4 — Transform with dbt

The dbt project is installed in an isolated `uv` virtual environment. All commands use `uv run dbt` to ensure the correct version is always used.

```bash
cd dbt-project/
uv sync
cd dbt-project/taxi_rides_ny/
uv run dbt deps
uv run dbt debug
uv run dbt seed
uv run dbt run
uv run dbt test
```

### Phase 5 — Batch processing with Spark

Spark runs locally in WSL and processes data from local files. The GCS connector is not configured in this project — at this scale, dbt on BigQuery handles all production transformations more efficiently. The Spark notebooks serve as a demonstration of distributed processing skills and would be the natural extension point for larger datasets.

```bash
# Open a WSL terminal and navigate to the batch folder
cd batch/
jupyter notebook # python -m jupyter notebook
```


### Phase 6 — Dashboard
 
The dashboard is built with **Looker Studio** connected directly to the BigQuery marts. No data export needed — Looker Studio queries `mart_month_revenue` and `mart_zone_stats` in real time.

[View the NYC Taxi Analytics Dashboard →](https://datastudio.google.com/s/jHU9jI2t7bo)


## Lessons learned

**Docker port conflicts are real.**
This was my first time working with Docker in a data engineering context.
PostgreSQL's default port (5432) was unavailable for two reasons: a local
PostgreSQL instance already running on the host, and a second PostgreSQL
container used internally by Kestra occupying the same port within the Docker
network. The fix was mapping `pgdatabase` to port 5433 on the host
(`5433:5432` in `docker-compose.yml`), which also taught me that
multi-container setups require careful port planning from the start.

**Isolated environments prevent dependency hell.**
I set up the dbt project inside a `uv` virtual environment scoped to the
`dbt-project/` folder rather than installing dbt globally. This keeps the
dbt version and its dependencies completely isolated from the rest of the
project. Every dbt command runs as `uv run dbt ...`, which makes the setup
fully reproducible on any machine without version conflicts.


**WSL as a sandbox for incompatible runtimes.**
Spark 4.x requires Java 17, but my local machine runs a different Java version
needed by other projects. Installing Spark inside WSL solved the conflict cleanly —
WSL acts as an isolated Linux layer with its own Java installation, completely
independent from the Windows host.


## Data Source
 
[NYC TLC Trip Record Data](https://github.com/DataTalksClub/nyc-tlc-data/releases) via DataTalksClub GitHub releases:
 
- Yellow taxi: 2019–2020
- Green taxi: 2019–2020
