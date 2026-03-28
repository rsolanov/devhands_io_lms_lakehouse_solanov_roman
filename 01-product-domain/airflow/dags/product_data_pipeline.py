from __future__ import annotations

import pendulum
import os

from airflow.models.dag import DAG
from airflow.operators.empty import EmptyOperator
from airflow.providers.docker.operators.docker import DockerOperator

AWS_ACCESS_KEY_ID = os.getenv("MINIO_ROOT_USER", "minioadmin")
AWS_SECRET_ACCESS_KEY = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")
S3_ENDPOINT = os.getenv("S3_ENDPOINT", "http://minio:9000")
ICEBERG_CATALOG_URI = os.getenv("ICEBERG_CATALOG_URI", "http://lakekeeper:8181")
ICEBERG_WAREHOUSE_NAME = os.getenv("ICEBERG_WAREHOUSE_NAME", "product_dw")


with DAG(
    dag_id="product_data_generation",
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    catchup=False,
    schedule="0 2 * * *",
    tags=['product', 'data-contract', 'docker', 'spark', 'iceberg']
) as dag:

    start = EmptyOperator(task_id='start')

    SPARK_IMAGE_NAME = '01-product-domain-spark-master'

    run_data_generator_job = DockerOperator(
        task_id='run_data_generator_job',
        image='product-domain/spark-master:3.5.0',
        command=[
            "/opt/spark/bin/spark-submit",
            "--master", "spark://spark-master:7077",
            "/opt/spark/applications/data_generator.py"
        ],
        docker_url="unix://var/run/docker.sock",
        network_mode="lakehouse-shared",
        auto_remove='success',
        mount_tmp_dir=False,
        environment={
            "S3_ENDPOINT": os.getenv("S3_ENDPOINT", "http://minio:9000"),
            "AWS_ACCESS_KEY_ID": os.getenv("MINIO_ROOT_USER", "minioadmin"),
            "AWS_SECRET_ACCESS_KEY": os.getenv("MINIO_ROOT_PASSWORD", "minioadmin"),
            "AWS_REGION": os.getenv("AWS_REGION", "us-east-1"),
            "ICEBERG_CATALOG_URI": os.getenv("ICEBERG_CATALOG_URI", "http://lakekeeper:8181"),
            "ICEBERG_WAREHOUSE_NAME": os.getenv("ICEBERG_WAREHOUSE_NAME", "product_dw"),
            "MINIO_ROOT_USER": os.getenv("MINIO_ROOT_USER", "minioadmin"),
            "MINIO_ROOT_PASSWORD": os.getenv("MINIO_ROOT_PASSWORD", "minioadmin"),
        }
    )

    end = EmptyOperator(task_id='end')

    start >> run_data_generator_job >> end