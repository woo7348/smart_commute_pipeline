from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

with DAG(
    dag_id="smart_commute_bus_seoul_pipeline",
    start_date=datetime(2025, 11, 5),
    schedule=None,
    catchup=False,
) as dag:

    fetch_bus = BashOperator(
        task_id="fetch_bus_seoul",
        bash_command="python /opt/airflow/src/fetch_bus_seoul.py",
    )

    transform_bus = BashOperator(
        task_id="transform_bus_seoul",
        bash_command="python /opt/airflow/src/transform_bus_seoul.py",
    )

    load_bus = BashOperator(
        task_id="load_bus_seoul",
        bash_command="python /opt/airflow/src/load_bus_seoul.py",
    )

    fetch_bus >> transform_bus >> load_bus
