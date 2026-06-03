## Environment

dbt is installed in an isolated `uv` virtual environment scoped to this folder, avoiding conflicts with other Python tools in the project.

### Create a dbt project with `uv`

```bash
uv init --python=3.11
uv venv --python 3.11
uv add "dbt-core==1.8.1" "dbt-bigquery==1.8.1"
uv pip install .
```

### Initialize a new dbt project from scratch

```bash
dbt init project-name
```

### Resources

To learn and stay up to date with dbt:

- Start with the official [dbt Documentation](https://docs.getdbt.com/docs/introduction)
- For common questions and community answers, see [dbt Discourse](https://discourse.getdbt.com/)
- For the latest news, best practices, and development updates, read the [dbt Blog](https://blog.getdbt.com/)