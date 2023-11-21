import uuid
from typing import List, Optional, Tuple

from core.schemas.bigquery.tables import ScoringAsset, ScoringDataset, ScoringJob
from core.schemas.service_evaluator import EvaluatedServiceName
from core.services.bigquery_writer import BigQueryWriter
from google.cloud import bigquery, bigquery_storage

from service_evaluator.dataset_manager import DatasetManager


class ResultsWriter:
    def __init__(
        self,
        big_query_client: bigquery.Client,
        bigquery_storage_client: bigquery_storage.BigQueryReadClient,
        bigquery_writer: BigQueryWriter,
        service_name: EvaluatedServiceName,
        big_query_dataset_name: str,
        location: str,
    ):
        self.big_query_client = big_query_client
        self.bigquery_storage_client = bigquery_storage_client
        self.bigquery_writer = bigquery_writer
        self.service_name = service_name
        self.big_query_dataset_name = big_query_dataset_name
        self.location = location

    def _retrieve_dataset_instance_if_any(self, md5: str) -> Optional[ScoringDataset]:
        query_columns = ", ".join(
            [field.name for field in ScoringDataset.__fields__.values()]
        )
        query = f"""
        SELECT {query_columns}
        FROM `{ScoringDataset.__bigquery_tablename__}`
        WHERE md5 = "{md5}"
        """

        job_config = bigquery.QueryJobConfig(
            default_dataset=self.big_query_dataset_name
        )
        results = self.big_query_client.query(
            query, job_config=job_config, location=self.location
        ).to_dataframe(bqstorage_client=self.bigquery_storage_client)

        if len(results) == 0:
            return None

        if len(results) != 1:
            raise ValueError(
                f"Multiple datasets found with the same md5: '{md5}'. Aborting."
            )

        return ScoringDataset.parse_obj(results.to_dict(orient="records")[0])

    def build_scoring_dataset_instance(
        self, scoring_dataset: ScoringDataset
    ) -> Tuple[ScoringDataset, bool]:
        dataset = self._retrieve_dataset_instance_if_any(md5=scoring_dataset.md5)

        if dataset is not None:
            return dataset, False

        return scoring_dataset, True

    def build_scoring_job_instance(self, dataset_id: str) -> ScoringJob:
        return ScoringJob(
            service_name=self.service_name,
            scoring_id=str(uuid.uuid4()),
            dataset_id=dataset_id,
        )

    @staticmethod
    def build_scoring_asset_instances(
        scoring_id: str, asset_paths: List[str], scores: List[float]
    ) -> List[ScoringAsset]:
        return [
            ScoringAsset(scoring_id=scoring_id, path=asset_path, score=score)
            for asset_path, score in zip(asset_paths, scores)
        ]

    def submit(self, dataset_manager: DatasetManager, scores: List[float]):
        if len(dataset_manager.asset_paths) != len(scores):
            raise RuntimeError("asset paths and scores should have the same lengths")

        scoring_dataset, is_new_dataset = self.build_scoring_dataset_instance(
            dataset_manager.scoring_dataset
        )

        scoring_job = self.build_scoring_job_instance(dataset_id=scoring_dataset.id)
        # pylint: disable=no-member
        scoring_assets = self.build_scoring_asset_instances(
            scoring_id=scoring_job.id,
            asset_paths=list(dataset_manager.asset_paths),
            scores=scores,
        )

        if is_new_dataset is True:
            self.bigquery_writer.submit([scoring_dataset])

        self.bigquery_writer.submit([scoring_job])
        self.bigquery_writer.submit(scoring_assets)
