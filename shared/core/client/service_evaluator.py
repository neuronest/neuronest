from __future__ import annotations

import datetime
import json
import time
from typing import Optional

from google.cloud import bigquery, bigquery_storage

from core.client.base import CloudRunBasedClient, HTTPClient
from core.exceptions import JobNotFoundError
from core.google.firestore_client import FirestoreClient
from core.routes.service_evaluator import routes
from core.schemas.bigquery.tables import ScoringAsset, ScoringJob
from core.schemas.service_evaluator import (
    EvaluateJobDocument,
    EvaluateResultsDocument,
    ResourcesOutput,
    ServiceEvaluatorInput,
    ServiceEvaluatorOutput,
)


class ServiceEvaluatorClient(HTTPClient, CloudRunBasedClient):
    def __init__(
        self,
        host: str,
        key_path: Optional[str] = None,
        project_id: Optional[str] = None,
    ):
        super().__init__(
            host=host, key_path=key_path, root=routes.root, project_id=project_id
        )
        self.firestore_client = FirestoreClient(
            key_path=self.key_path, project_id=project_id
        )
        # noinspection PyTypeChecker
        self.bigquery_client = bigquery.Client(project=self.project_id)
        self.bigquery_storage_client = (
            bigquery_storage.BigQueryReadClient()
            if key_path is None
            else bigquery_storage.BigQueryReadClient.from_service_account_json(key_path)
        )

    @classmethod
    def from_primitive_attributes(cls, **kwargs) -> ServiceEvaluatorClient:
        mandatory_fields = "host"
        optional_fields = ("key_path", "project_id")

        try:
            (host,) = [kwargs[mandatory_field] for mandatory_field in mandatory_fields]
        except KeyError as key_error:
            raise ValueError(
                f"At least one mandatory field is missing, expected fields: "
                f"{mandatory_fields}"
            ) from key_error

        optional_values = {
            optional_field: kwargs[optional_field]
            for optional_field in optional_fields
            if optional_field in kwargs
        }

        return cls(
            host=host,
            **optional_values,
        )

    def _get_region(self) -> str:
        return ResourcesOutput(
            **json.loads(
                self.call(
                    resource=f"/{routes.Resources.prefix}" f"{routes.Resources.region}",
                    verb="get",
                ).text
            )
        ).resource

    def _get_firestore_jobs_collection(self) -> str:
        return ResourcesOutput(
            **json.loads(
                self.call(
                    resource=f"/{routes.Resources.prefix}"
                    f"{routes.Resources.firestore_jobs_collection}",
                    verb="get",
                ).text
            )
        ).resource

    def _get_bigquery_dataset_name(self) -> str:
        return ResourcesOutput(
            **json.loads(
                self.call(
                    resource=f"/{routes.Resources.prefix}"
                    f"{routes.Resources.bigquery_dataset_name}",
                    verb="get",
                ).text
            )
        ).resource

    @staticmethod
    def _build_results_query(job_id: str) -> str:
        return f"""
            select
                scoring_job.id as job_id,
                scoring_job.dataset_id,
                # job_date,
                service_name,
                service_image_name,
                metric_name,
                array_agg(scoring_id) as scoring_ids,
                array_agg(path) as paths,
                array_agg(score) as scores
            from
                {ScoringJob.__bigquery_tablename__} scoring_job
            join
                {ScoringAsset.__bigquery_tablename__} scoring_asset
            on
                scoring_job.id = scoring_asset.scoring_id
            where
                scoring_job.id = {job_id}
        """

    def _get_results(
        self,
        job_id: str,
        wait_if_not_existing: bool,
        timeout: int,
        retry_wait_time: int = 60,
        total_waited_time: int = 0,
    ) -> EvaluateResultsDocument:
        bigquery_dataset_name, region = (
            self._get_bigquery_dataset_name(),
            self._get_region(),
        )

        job_config = bigquery.QueryJobConfig(
            default_dataset=f"{self.bigquery_client.project}.{bigquery_dataset_name}"
        )

        query = self._build_results_query(job_id=job_id)

        results = (
            self.bigquery_client.query(query, job_config=job_config, location=region)
            .to_dataframe(bqstorage_client=self.bigquery_storage_client)
            .to_dict(orient="records")
        )

        if len(results) != 1:
            raise ValueError(
                "Multiple rows found but should have been unique. Aborting."
            )

        if len(results) == 1:
            return EvaluateResultsDocument.parse_obj(results[0])

        if wait_if_not_existing is False:
            raise RuntimeError(f"No results found for job_id={job_id}")

        if total_waited_time + retry_wait_time > timeout:
            raise TimeoutError(
                f"Failed to retrieve predictions for job_id={job_id},"
                f"giving up after {timeout // 60} minutes of trying"
            )

        time.sleep(retry_wait_time)
        total_waited_time += retry_wait_time

        return self._get_results(
            job_id=job_id,
            wait_if_not_existing=wait_if_not_existing,
            timeout=timeout,
            retry_wait_time=retry_wait_time,
            total_waited_time=total_waited_time,
        )

    def _run_evaluation(
        self, reuse_already_computed_results: bool = True
    ) -> ServiceEvaluatorOutput:
        return ServiceEvaluatorOutput(
            **json.loads(
                self.call(
                    resource=f"/{routes.Evaluator.prefix}{routes.Evaluator.evaluate}",
                    verb="post",
                    payload=ServiceEvaluatorInput(
                        reuse_already_computed_results=reuse_already_computed_results
                    ).dict(),
                ).text
            )
        )

    def get_predictions_from_job_id(
        self,
        job_id: str,
        wait_if_not_existing: bool = False,
        job_timeout: int = 2700,
    ) -> EvaluateResultsDocument:
        raw_job_document = self.firestore_client.get_document(
            collection_name=self._get_firestore_jobs_collection(),
            document_id=job_id,
        )

        if raw_job_document is None:
            raise JobNotFoundError(f"No document found for job_id={job_id}")

        job_document = EvaluateJobDocument.parse_obj(raw_job_document)
        job_time_delta = max(
            (
                job_timeout
                - (datetime.datetime.utcnow() - job_document.job_date).seconds
            ),
            0,
        )

        try:
            return self._get_results(
                job_id=job_id,
                wait_if_not_existing=wait_if_not_existing,
                timeout=job_time_delta,
            )
        except TimeoutError as timeout_error:
            raise TimeoutError(
                f"At least one asset results could not be retrieved in time "
                f"(targeted job UTC date: {job_document.job_date})"
            ) from timeout_error

    def evaluate_async(
        self,
    ) -> ServiceEvaluatorOutput:
        return self._run_evaluation()

    def evaluate_sync(
        self,
    ) -> EvaluateResultsDocument:
        service_evaluator_output = self._run_evaluation()

        return self.get_predictions_from_job_id(service_evaluator_output.job_id)
