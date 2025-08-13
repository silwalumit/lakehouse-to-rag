"""
Lakehouse ETL Pipeline DAG

This DAG implements a complete data pipeline from scraping to gold table:
- Scrapes websites and saves to MinIO
- Transforms data using Spark
- Writes to Delta Lake tables (bronze -> silver -> gold)
"""

import json
import os
import sys
from datetime import timedelta
from logging import getLogger
from typing import Any, Dict, List

import duckdb
import pyarrow as pa
from deltalake import DeltaTable, write_deltalake

# Add project paths

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

# Data processing imports
from docker.types import Mount

from airflow import DAG
from airflow.models import Variable

# from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.utils.dates import days_ago
from config.settings import Settings
from helpers.minio_service import MinioIOService

settings = Settings()


logger = getLogger(__name__)


STORAGE_OPTIONS = {
    "AWS_ACCESS_KEY_ID": "minioadmin",
    "AWS_SECRET_ACCESS_KEY": "minioadmin",
    "AWS_ENDPOINT_URL": "http://minio:9000",  # MinIO S3 endpoint
    "AWS_S3_VERIFY_SSL": "false",
    "AWS_ALLOW_HTTP": "true",
}


def extract_raw_data() -> List[Dict[str, Any]]:
    """Extract data from MinIO bronze bucket."""
    logger.info("Extracting data from MinIO bronze bucket")

    records = []

    try:
        minio_client = MinioIOService(
            endpoint="minio:9000",
            access_key=settings.minio.access_key,
            secret_key=settings.minio.secret_key.get_secret_value(),
        )

        # List objects in bronze bucket
        objects = minio_client.list_objects("raw")

        for obj in objects:
            if obj.object_name.endswith(".json"):
                # Download and parse JSON data
                if raw_data := minio_client.download("raw", obj.object_name):
                    data = json.loads(raw_data.decode("utf-8"))
                    data["source"] = obj.object_name
                    records.append(data)

        logger.info(f"Extracted {len(records)} records from bronze bucket")
        return records

    except Exception as e:
        logger.error(f"Failed to extract bronze data: {e}")
        return []


def bronze_transform(**kwargs) -> None:
    """Transform raw data to bronze table."""
    logger.info("Starting bronze transform")
    try:
        records = extract_raw_data()
        if not records:
            logger.warning("No records found in bronze bucket")
            return

        arrow_table = pa.Table.from_pylist(records)
        connection = duckdb.connect()
        connection.register("raw", arrow_table)

        bronze_df = connection.execute("""
            SELECT
                url,
                source,
                title,
                TRIM(content) AS content,
                NOW()::TIMESTAMP AS processed_at,
                LENGTH(TRIM(content)) AS content_length
            FROM raw
            WHERE content IS NOT NULL AND LENGTH(TRIM(content)) > 0
        """).arrow()

        write_deltalake(
            "s3://datalake/bronze",
            bronze_df,
            mode="overwrite",
            storage_options=STORAGE_OPTIONS,
        )

    except Exception as e:
        logger.error(f"Bronze transform failed: {e}")
        raise


def silver_transform():
    logger.info("Starting silver transform")

    try:
        # Load Delta table into DuckDB via delta-rs
        table = DeltaTable("s3://datalake/bronze", storage_options=STORAGE_OPTIONS)
        bronze_df = table.to_pyarrow_table()

        # Transform bronze to silver
        silver_pa = transform_bronze_to_silver(bronze_df, min_content_length=50)

        # Write to Delta using delta-rs
        write_deltalake(
            "s3://datalake/silver",
            silver_pa,
            mode="overwrite",
            storage_options=STORAGE_OPTIONS,
        )

    except Exception as e:
        logger.error(f"Silver transform failed: {e}")
        raise


def transform_bronze_to_silver(
    bronze_df: pa.Table,
    min_content_length: int = 50,
) -> pa.Table:
    """
    Transform bronze data to silver format.
    Removes duplicate row by url
    """
    con = duckdb.connect()
    con.register("bronze", bronze_df)

    query = f"""
        WITH cleaned AS (
            SELECT 
                *,
                TRIM(
                    REGEXP_REPLACE(
                        LOWER(
                            REGEXP_REPLACE(
                                content,
                                '[^\\w\\d\\s\\.,!?;:\\-\\(\\)]',
                                ' ',
                                'g'
                            )
                        ),
                        '\\s+',
                        ' ',
                        'g'
                    )
                ) AS cleaned_content
            FROM bronze
            WHERE content IS NOT NULL
        ),
        ranked AS (
            SELECT
                *,
                ROW_NUMBER() OVER (
                    PARTITION BY url
                    ORDER BY processed_at
                ) AS row_number
            FROM cleaned
            WHERE LENGTH(cleaned_content) > {min_content_length}
        )
        SELECT
            url,
            source,
            title,
            cleaned_content AS content,
            processed_at,
            NOW()::TIMESTAMP AS silver_processed_at,
            LENGTH(cleaned_content) AS content_length
        FROM ranked
        WHERE row_number = 1
    """

    silver_df = con.execute(query).arrow()

    con.close()
    return silver_df


def _split_content(content: str) -> List[str]:
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=200,
        chunk_overlap=10,
        add_start_index=True,
    )
    return splitter.split_text(content)


def gold_transform():
    """Transform silver data to gold table."""
    logger.info("Starting gold transform")

    try:
        # Read from silver Delta table into PyArrow
        silver_table = DeltaTable(
            "s3://datalake/silver",
            storage_options=STORAGE_OPTIONS,
        )
        silver_df = silver_table.to_pandas()

        gold_df = silver_df.copy()
        gold_df["chunks"] = gold_df["content"].apply(_split_content)
        gold_df = (
            gold_df.explode("chunks")
            .rename(columns={"chunks": "chunk"})
            .reset_index(drop=True)
        )

        # Write to Delta using delta-rs
        write_deltalake(
            "s3://datalake/silver",
            gold_df,
            mode="overwrite",
            storage_options=STORAGE_OPTIONS,
        )

        logger.info(f"Gold transform completed: {gold_df.num_rows} rows")

    except Exception as e:
        logger.error(f"Gold transform failed: {e}")
        raise


with DAG(
    dag_id="lakehouse_etl_pipeline",
    description="Scrape, ETL, and embed pipeline",
    schedule_interval=None,
    start_date=days_ago(1),
    default_args={
        "owner": "airflow",
        "depends_on_past": False,
        "retries": 0,
        "retry_delay": timedelta(minutes=1),
    },
    catchup=False,
):
    start_url = Variable.get("start_url", None)
    selectors = Variable.get("selectors", None)
    max_pages = int(Variable.get("max_pages", 0))

    scrape_task = DockerOperator(
        task_id="run_scrapper",
        image="webscraper:latest",
        api_version="auto",
        auto_remove="force",
        docker_url="unix://var/run/docker.sock",
        network_mode="host",
        mounts=[
            Mount(
                source="/Users/sputnik/Developer/lakehouse-to-rag/sample_config/config.yaml",
                target="/app/config.yaml",
                type="bind",
                read_only=True,
            ),
        ],
        command=["--config", "config.yaml"],
        environment=dict(os.environ),
    )

    bronze = PythonOperator(
        task_id="bronze_transform",
        python_callable=bronze_transform,
        provide_context=True,
    )

    silver = PythonOperator(
        task_id="silver",
        python_callable=silver_transform,
        provide_context=True,
    )
    scrape_task >> bronze >> silver
