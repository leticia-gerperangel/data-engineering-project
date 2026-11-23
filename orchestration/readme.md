## Kestra

[Kestra](https://kestra.io/) is an open-source, declarative workflow orchestration platform used to build, schedule, monitor, and govern automated data pipelines.

Workflows are defined as YAML files. Main concepts:
- [Flow](https://go.kestra.io/de-zoomcamp/flow) - a container for tasks and their orchestration logic.
- [Tasks](https://go.kestra.io/de-zoomcamp/tasks) - the steps within a flow.
- [Inputs](https://go.kestra.io/de-zoomcamp/inputs) - dynamic values passed to the flow at runtime.
- [Outputs](https://go.kestra.io/de-zoomcamp/outputs) - pass data between tasks and flows.
- [Triggers](https://go.kestra.io/de-zoomcamp/triggers) - mechanism that automatically starts the execution of a flow.
- [Execution](https://go.kestra.io/de-zoomcamp/execution) - a single run of a flow with a specific state.
- [Variables](https://go.kestra.io/de-zoomcamp/variables) - key–value pairs that let you reuse values across tasks.
- [Plugin Defaults](https://go.kestra.io/de-zoomcamp/plugin-defaults) - default values applied to every task of a given type within one or more flows.
- [Concurrency](https://go.kestra.io/de-zoomcamp/concurrency) - control how many executions of a flow can run at the same time.

In this project, the flows download the NYC taxi CSV files and load them into PostgreSQL, and into GCS and BigQuery.

| Flow | Purpose |
|---|---|
|[`01-hello-world.yaml`](01-hello-world.yaml) | Showcases all of these concepts inside of one workflow. |
|[`02-python.yaml`](02-python.yaml) | Example of Python workflow. |
|[`03-getting-started-pipeline.yaml`](03-getting-started-pipeline.yaml) | Demonstrate a simple data pipeline which extracts data via HTTP REST API, transforms that data in Python and then queries it using DuckDB. |
|[`04-postgres-taxi`](04-postgres-taxi.yaml) | Extract CSV data partitioned by year and month, create tables, load data to the monthly table, and finally merge the data to the final destination table. |
| `06-gcp-kv-example` | Register GCP values in the Kestra KV store. Run manually from the UI. |
| `07-gcp-setup` | Create the GCS bucket and BigQuery dataset |
| `08-gcp-taxi` | Extract CSV Data → Upload to GCS → BigQuery external + partitioned tables + MERGE |