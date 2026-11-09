# Walmart dbt and Airflow

This project uses dbt Core and the Databricks adapter to transform Walmart data,
with Apache Airflow orchestrating ingestion and dbt tasks.

## Data workflow

The `orchestrate` DAG in `airflow/dags/orchestrator.py` runs these tasks in order:

1. Trigger and monitor the Databricks CDC ingestion job.
2. Check dbt source freshness.
3. Build the `silver_t` models and run their tests.
4. Build the `silver_b` model.
5. Run dbt snapshots.
6. Build the gold fact model.

The dbt project is in `walmart_project/`. It reads bronze tables defined in
`models/sources.yml`, builds the silver and gold models, and defines customer,
employee, order, product, and store snapshots.

## Requirements

- Python 3.13
- [uv](https://docs.astral.sh/uv/)
- Docker Desktop with Docker Compose
- Databricks workspace access and a CDC job

The locked versions are dbt Core 1.12.6 and dbt-databricks 1.13.0. On Windows,
run Airflow through Docker rather than directly in the Windows Python
environment.

## Configure credentials

Both `profiles.yml` files read the Databricks token from the
`DATABRICKS_TOKEN` environment variable. Never commit tokens or other secrets.

For Airflow, create `airflow/.env` (this file is ignored by Git) and provide:

```dotenv
AIRFLOW_UID=50000
FERNET_KEY=<a-valid-airflow-fernet-key>
DATABRICKS_TOKEN=<your-databricks-token>
_AIRFLOW_WWW_USER_USERNAME=airflow
_AIRFLOW_WWW_USER_PASSWORD=<choose-a-local-password>
```

Use a unique, valid Fernet key and a strong local Airflow password; do not use
the example values for a shared or production deployment. Compose passes these
environment variables to its Airflow containers.

Before enabling the DAG, configure the workspace host and job ID in
`airflow/dags/orchestrator.py`. Update the CDC task to read its token from the
`DATABRICKS_TOKEN` environment variable instead of hard-coding it. The dbt
profiles already use that environment variable.

For local dbt commands in PowerShell, set the token for the current session:

```powershell
$env:DATABRICKS_TOKEN = "<your-databricks-token>"
```

## Run Airflow

From the repository root, initialize the Airflow services and start the stack:

```powershell
Set-Location airflow
docker compose up airflow-init
docker compose up -d
```

Open [http://localhost:8080](http://localhost:8080) and sign in with the
username and password configured in `airflow/.env`. Check service status and
logs with:

```powershell
docker compose ps
docker compose logs -f airflow-scheduler airflow-dag-processor
```

Stop the stack while preserving its database volume with:

```powershell
docker compose down
```

## Run dbt locally (optional)

From the repository root, sync the locked Python dependencies and run dbt with
the root project's profile:

```powershell
uv venv --python 3.13 .venv-py313
$env:UV_PROJECT_ENVIRONMENT = Join-Path $PWD ".venv-py313"
uv sync --locked
$env:DATABRICKS_TOKEN = "<your-databricks-token>"
uv run --locked dbt --project-dir walmart_project --profiles-dir walmart_project debug
uv run --locked dbt --project-dir walmart_project --profiles-dir walmart_project build
```

## Repository layout

```text
airflow/
  dags/orchestrator.py       Airflow DAG
  docker-compose.yaml        Local Airflow stack
  walmart_project/           dbt project mounted into Airflow
walmart_project/
  models/                    Sources, silver transformations, and gold models
  snapshots/                 Slowly changing dimension snapshots
  tests/                     dbt tests
pyproject.toml               Python dependencies and project metadata
uv.lock                      Locked dependency versions
```

The root and Airflow dbt directories are separate project copies. Keep their
models and configuration in sync when changing dbt behavior used by Airflow.