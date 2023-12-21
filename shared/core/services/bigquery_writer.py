from typing import List

from google.cloud import bigquery

from core.schemas.bigquery.base import BigQueryModel


class BigQueryWriter:
    def __init__(
        self,
        dataset_name: str,
        big_query_client: bigquery.Client,
        location: str,
        timeout: int = 30,
    ):
        self.dataset_name = dataset_name
        self.big_query_client = big_query_client
        self.location = location
        self.timeout = timeout

    @property
    def project_id(self) -> str:
        return self.big_query_client.project

    @property
    def project_id_dot_dataset_name(self) -> str:
        # we explicitly create a variable {PROJECT_ID}.{DATASET_NAME}
        # rather than calling it DATASET_NAME, which is confusing
        return f"{self.project_id}.{self.dataset_name}"

    @staticmethod
    def _load_job_config_from_schema(
        schema: List[bigquery.SchemaField],
    ) -> bigquery.LoadJobConfig:
        return bigquery.LoadJobConfig(
            schema=schema,
            write_disposition="WRITE_APPEND",
        )

    def get_or_create_dataset(self) -> bigquery.Dataset:
        dataset = bigquery.Dataset(dataset_ref=self.project_id_dot_dataset_name)
        dataset.location = self.location

        return self.big_query_client.create_dataset(
            dataset, timeout=self.timeout, exists_ok=True
        )

    def submit(self, rows: List[BigQueryModel]):
        if len(rows) == 0:
            return

        first_row = rows[0]
        bigquery_table_name = first_row.__bigquery_tablename__
        if any(bigquery_table_name != row.__bigquery_tablename__ for row in rows):
            raise ValueError("All rows should have the same bigquery table name")

        schema = first_row.to_big_query_fields()

        dataset = self.get_or_create_dataset()

        self.big_query_client.create_table(
            bigquery.Table(
                dataset.table(bigquery_table_name),
                schema=schema,
            ),
            timeout=self.timeout,
            exists_ok=True,
        )

        self.big_query_client.load_table_from_json(
            json_rows=[row.dict() for row in rows],
            destination=f"{self.project_id_dot_dataset_name}.{bigquery_table_name}",
            job_config=self._load_job_config_from_schema(schema),
        )
