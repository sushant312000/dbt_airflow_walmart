# dbt Airflow Walmart

## Databricks credentials

Both dbt profiles read the Databricks access token from the `DATABRICKS_TOKEN`
environment variable. Do not put credentials in `profiles.yml` or commit them.

- For Airflow Compose, set `DATABRICKS_TOKEN` in `airflow/.env`. That file is
  local-only and ignored by Git.
- For local dbt commands in PowerShell, set it for the current session:
  `$env:DATABRICKS_TOKEN = "<your-token>"`.