import uuid
from typing import Dict, List, Optional, Tuple, Type, Union

from core.schemas.bigquery.base import BigQueryModel
from core.schemas.bigquery.tables import (
    PredictionAsset,
    ScoringAsset,
    ScoringDataset,
    ScoringJob,
)
from core.schemas.image_name import ImageNameWithTag
from core.schemas.service_evaluator import EvaluatedServiceName
from core.services.bigquery_writer import BigQueryWriter
from google.api_core.exceptions import NotFound
from google.cloud import bigquery, bigquery_storage

from service_evaluator.dataset_manager import DatasetManager
from service_evaluator.scorer.base import ScorableDocument
from service_evaluator.scorer.metrics import MetricName


class ResultsHandler:
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

    def _retrieve_instance_if_any(
        self,
        bigquery_model: Type[BigQueryModel],
        fields_conditions: Dict[str, str],
        ensure_unicity: bool = False,
    ) -> Optional[Union[List[BigQueryModel], BigQueryModel]]:
        query_columns = ", ".join(
            [field.name for field in bigquery_model.__fields__.values()]
        )
        query_conditions = "WHERE " + " AND ".join(
            [f"{name}='{value}'" for name, value in fields_conditions.items()]
        )
        query = f"""
        SELECT {query_columns}
        FROM `{bigquery_model.__bigquery_tablename__}`
        {query_conditions}
        """

        job_config = bigquery.QueryJobConfig(
            default_dataset=(
                f"{self.big_query_client.project}.{self.big_query_dataset_name}"
            )
        )

        try:
            results = (
                self.big_query_client.query(
                    query, job_config=job_config, location=self.location
                )
                .to_dataframe(bqstorage_client=self.bigquery_storage_client)
                .to_dict(orient="records")
            )
        except NotFound:
            return None

        if len(results) == 0:
            return None

        if len(results) != 1:
            if ensure_unicity is True:
                raise ValueError(
                    "Multiple rows found but should have been unique. Aborting."
                )

            return bigquery_model.parse_obj(results)

        return bigquery_model.parse_obj(results[0])

    def _retrieve_dataset_instance_if_any(self, md5: str) -> Optional[ScoringDataset]:
        return self._retrieve_instance_if_any(
            bigquery_model=ScoringDataset,
            fields_conditions={"md5": md5},
            ensure_unicity=True,
        )

    def _retrieve_jobs_instances_if_any(
        self, service_image_name: ImageNameWithTag, dataset_id: str
    ) -> Optional[List[ScoringJob]]:
        return self._retrieve_instance_if_any(
            bigquery_model=ScoringJob,
            fields_conditions={
                "service_image_name": service_image_name,
                "dataset_id": dataset_id,
            },
            ensure_unicity=False,
        )

    def _retrieve_predictions_instances_if_any(
        self, scoring_id: str
    ) -> Optional[List[PredictionAsset]]:
        return self._retrieve_instance_if_any(
            bigquery_model=PredictionAsset,
            fields_conditions={
                "scoring_id": scoring_id,
            },
            ensure_unicity=False,
        )

    def build_scoring_dataset_instance(
        self, scoring_dataset: ScoringDataset
    ) -> Tuple[ScoringDataset, bool]:
        dataset = self._retrieve_dataset_instance_if_any(md5=scoring_dataset.md5)

        if dataset is not None:
            return dataset, False

        return scoring_dataset, True

    def build_scoring_job_instance(
        self,
        dataset_id: str,
        service_image_name: ImageNameWithTag,
        metric_name: MetricName,
    ) -> ScoringJob:
        return ScoringJob(
            service_name=self.service_name,
            service_image_name=service_image_name,
            metric_name=metric_name,
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

    @staticmethod
    def build_prediction_asset_instances(
        scoring_id: str,
        asset_paths: List[str],
        prediction_documents: List[ScorableDocument],
    ) -> List[PredictionAsset]:
        return [
            PredictionAsset(
                scoring_id=scoring_id,
                path=asset_path,
                serialized_prediction=prediction_document.json(),
            )
            for asset_path, prediction_document in zip(
                asset_paths, prediction_documents
            )
        ]

    def read_existing_predictions(
        self,
        dataset_manager: DatasetManager,
        service_image_name: ImageNameWithTag,
        scorable_document_class: Type[ScorableDocument],
    ) -> List[ScorableDocument]:
        scoring_dataset, _ = self.build_scoring_dataset_instance(
            dataset_manager.scoring_dataset
        )

        jobs_instances = self._retrieve_jobs_instances_if_any(
            service_image_name=service_image_name, dataset_id=scoring_dataset.id
        )

        if jobs_instances is None or len(jobs_instances) == 0:
            return []

        latest_matching_job = sorted(
            jobs_instances,
            key=lambda job_instance: job_instance.created_date,
            reverse=True,
        )[0]

        predictions_instances = self._retrieve_predictions_instances_if_any(
            scoring_id=latest_matching_job.scoring_id
        )

        if predictions_instances is None:
            return []

        return [
            scorable_document_class.parse_raw(prediction_instance.serialized_prediction)
            for prediction_instance in predictions_instances
        ]

    def write_predictions_and_scores(
        self,
        dataset_manager: DatasetManager,
        service_image_name: ImageNameWithTag,
        prediction_documents: List[ScorableDocument],
        metric_name: MetricName,
        scores: List[float],
    ):
        if not (
            len(dataset_manager.asset_paths) == len(prediction_documents) == len(scores)
        ):
            raise RuntimeError(
                "asset paths, prediction_documents and scores should have the same "
                "lengths"
            )

        scoring_dataset, is_new_dataset = self.build_scoring_dataset_instance(
            dataset_manager.scoring_dataset
        )

        scoring_job = self.build_scoring_job_instance(
            dataset_id=scoring_dataset.id,
            service_image_name=service_image_name,
            metric_name=metric_name,
        )
        # pylint: disable=no-member
        scoring_assets = self.build_scoring_asset_instances(
            scoring_id=scoring_job.id,
            asset_paths=list(dataset_manager.asset_paths),
            scores=scores,
        )
        prediction_assets = self.build_prediction_asset_instances(
            scoring_id=scoring_job.id,
            asset_paths=list(dataset_manager.asset_paths),
            prediction_documents=prediction_documents,
        )

        if is_new_dataset is True:
            self.bigquery_writer.submit([scoring_dataset])

        self.bigquery_writer.submit([scoring_job])
        self.bigquery_writer.submit(scoring_assets)
        self.bigquery_writer.submit(prediction_assets)
