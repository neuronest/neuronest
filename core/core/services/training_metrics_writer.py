from typing import List

from google.cloud import bigquery

from neuronest.core.schemas.training_metrics.tables import TrainingMetrics


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
        dataset = bigquery.Dataset(self.dataset_name)
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
            destination=f"{self.dataset_name}."
            f"{training_metrics.__bigquery_tablename__}",
            job_config=self._load_job_config_from_schema(
                training_metrics.to_big_query_fields()
            ),
        )
