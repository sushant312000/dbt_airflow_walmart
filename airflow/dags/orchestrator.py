from airflow.sdk import dag, task
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.jobs import RunLifeCycleState, RunResultState
import time

@dag
def orchestrate():

    @task
    def ingest_cdc():
        ws = WorkspaceClient(
        host="your_databricks_host",
        token="your_databricks_token"
        )

        job_trigger = ws.jobs.run_now(job_id="your_databricks_job_id")

        while True:

            job_run = ws.jobs.get_run(job_trigger.run_id)

            if job_run.state.life_cycle_state in [RunLifeCycleState.TERMINATED, RunLifeCycleState.SKIPPED, RunLifeCycleState.INTERNAL_ERROR]:
                if job_run.state.result_state == RunResultState.SUCCESS:
                    print("Job completed successfully!")
                    break 
                else:
                    raise Exception(f"Job failed with state: {job_run.state.result_state}")
                    
            time.sleep(5)  # Wait for 5 seconds before checking the job status again
        
        return "CDC ingestion completed"

    @task.bash
    def source_freshness():
        return "cd /opt/airflow/walmart_project && dbt source freshness --no-partial-parse"

    @task.bash
    def run_silver_t():
        return "cd /opt/airflow/walmart_project && dbt run --select silver_t"

    @task.bash
    def run_silver_tests():
        return "cd /opt/airflow/walmart_project && dbt test --select silver_t"

    @task.bash
    def run_silver_b():
        return "cd /opt/airflow/walmart_project && dbt run --select silver_b"

    @task.bash
    def gold_dim():
        return "cd /opt/airflow/walmart_project && dbt snapshot"

    @task.bash
    def gold_fact():
        return "cd /opt/airflow/walmart_project && dbt run --select path:models/gold/fact"

    ingest_cdc() >> source_freshness() >> run_silver_t() >> run_silver_tests() >> run_silver_b() >> gold_dim() >> gold_fact()   

orchestrate_dag = orchestrate()
