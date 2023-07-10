from typing import List

from google.cloud import bigquery

from core.schemas.training_metrics.tables import TrainingMetrics


class MetricsWriter:
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
        # noinspection PyTypeChecker
        dataset = bigquery.Dataset(dataset_ref=self.project_id_dot_dataset_name)
        dataset.location = self.location

        return self.big_query_client.create_dataset(
            dataset, timeout=self.timeout, exists_ok=True
        )

    def submit(self, training_metrics: TrainingMetrics):
        dataset = self.get_or_create_dataset()

        self.big_query_client.create_table(
            bigquery.Table(
                dataset.table(training_metrics.__bigquery_tablename__),
                schema=training_metrics.to_big_query_fields(),
            ),
            timeout=self.timeout,
            exists_ok=True,
        )

        self.big_query_client.load_table_from_json(
            json_rows=[training_metrics.dict()],
            destination=f"{self.project_id_dot_dataset_name}."
            f"{training_metrics.__bigquery_tablename__}",
            job_config=self._load_job_config_from_schema(
                training_metrics.to_big_query_fields()
            ),
        )
