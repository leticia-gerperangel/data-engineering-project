## Docker and local ingestion

- **Infrastructure (required by the project).** Docker Compose starts the containers used by the whole project: PostgreSQL, pgAdmin and Kestra. Kestra runs the flows of the ELT pipeline (Phase 2 in the [main README](../README.md)), so this infrastructure has to be running before the pipeline can be executed.
- **Ingestion script (learning exercise).** It practices Docker and builds a small ingestion pipeline: download NYC taxi CSV data from the web, load it into PostgreSQL and process large files in chunks. The script is not part of the ELT pipeline that feeds the dashboard.

## Infrastructure
 
`containers/docker-compose.yml` defines the local environment:
 
| Service | Role |
|---|---|
| PostgreSQL (`pgdatabase`) | Local database. Target of the ingestion script and of the Kestra flow `04-postgres-taxi` |
| pgAdmin | Web interface to inspect PostgreSQL |
| Kestra | Workflow orchestrator. Runs the flows of the ELT pipeline, with its own PostgreSQL database as backend | 

## Ingestion script
 
`ingest_data.py` downloads one month of yellow or green taxi data and loads it into a PostgreSQL table. It reads the file with pandas applying explicit column types and parsing the date columns, and loads it in blocks of rows (chunks).

### Ingest NYC taxi data into PostgreSQL

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
 
## Why it is built this way
 
- **Docker Compose.** A single configuration file starts the whole local environment, so it is reproducible with one command, and the services reach each other by name on the same Docker network.
- **Dockerfile.** It packages the ingestion script so it runs in the same environment as the database, on the same Docker network.
- **Chunks.** Monthly files are large. Reading and loading them in blocks keeps memory usage bounded instead of loading the whole file at once.
- **Explicit column types.** The types are defined in `schemas.py` instead of being inferred, so the table schema stays consistent from one month to the next.
- **Notebook first, script later.** The ingestion was prototyped in a notebook and then converted into a command-line script, so it can be reused with different parameters and containerized.
- **Limitation.** The script appends to the table, so loading the same month twice duplicates its rows. The idempotent version of this load (staging table + MERGE) is the Kestra flow `04-postgres-taxi`.


## Notebook workflow
 
The notebook is converted into a script, and its outputs are cleared before committing. Cell outputs are stored in the file and can expose local paths.
 
```bash
uv run jupyter nbconvert --to=script notebook.ipynb
mv notebook.py ingest_data.py
 
uv run python -m jupyter nbconvert --clear-output --inplace notebook.ipynb
```
