from __future__ import annotations

import os
import pendulum
from datetime import timedelta

from airflow.models.dag import DAG
from airflow.operators.empty import EmptyOperator
from airflow.providers.docker.operators.docker import DockerOperator

DBT_IMAGE = "platform-dbt:latest"

DBT_PROJECT_DIR  = "/usr/app/dbt"
DBT_PROFILES_DIR = "/root/.dbt"
DBT_COMMAND = "build"
DBT_ARGS = f"--profiles-dir {DBT_PROFILES_DIR} --project-dir {DBT_PROJECT_DIR}"

DBT_PROJECT_HOST_PATH  = os.getenv(
    "DBT_PROJECT_HOST_PATH",
    "/opt/airflow/dbt/dbt_project"
)
DBT_PROFILES_HOST_PATH = os.getenv(
    "DBT_PROFILES_HOST_PATH",
    "/opt/airflow/dbt/profiles.yml"
)

default_args = {
    "owner": "platform-team",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="dbt_platform_transformation",
    default_args=default_args,
    description="Transform data using dbt",
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    schedule="0 3 * * *",
    catchup=False,
    tags=["platform", "dbt", "transformation"],
) as dag:

    start = EmptyOperator(task_id="start")

    dbt = DockerOperator(
        task_id="dbt",
        image=DBT_IMAGE,
        command=["dbt"] + DBT_COMMAND.split() + DBT_ARGS.split(),
        docker_url="unix://var/run/docker.sock",
        network_mode="lakehouse-shared",
        auto_remove="success",
        mount_tmp_dir=False,
        force_pull=False,
        environment={
            "DBT_TRINO_HOST":     os.getenv("TRINO_HOST",     "trino-coordinator"),
            "DBT_TRINO_PORT":     os.getenv("TRINO_PORT",     "8080"),
            "DBT_TRINO_USER":     os.getenv("TRINO_USER",     "admin"),
            "DBT_TRINO_DATABASE": os.getenv("TRINO_DATABASE", "iceberg_platform"),
            "DBT_TRINO_SCHEMA":   os.getenv("TRINO_SCHEMA",   "ods"),
        },
    )

    end = EmptyOperator(task_id="end")

    start >> dbt >> end