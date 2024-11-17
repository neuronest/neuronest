import datetime
import json
import time
from abc import ABC
from typing import Any, Dict, Iterable, List, Optional, Type

from core.client.abstract.api_client import APIClient
from core.exceptions import PredictionsNotFoundError
from core.google.firestore_client import FirestoreClient
from core.google.storage_client import StorageClient
from core.hashing import combine_hashes
from core.path import GSPath
from core.schemas.abstract.prediction_api_client import (
    GSSample,
    Input,
    JobDocument,
    JobResultsDocument,
    LocalSample,
    Output,
    RealTimeInput,
    RealTimeOutput,
    ResourcesOutput,
    SampleResultsDocument,
)
from core.tools import generate_file_id, get_chunks_from_iterable


def make_results_blob_name(
    job_id: str,
    sample_id: str,
) -> str:
    return combine_hashes([job_id, sample_id])


class PredictionAPIClient(APIClient, ABC):
    InputSchema: Type[Input]
    OutputSchema: Type[Output]
    RealTimeInputSchema: Type[RealTimeInput]
    RealTimeOutputSchema: Type[RealTimeOutput]
    JobDocumentSchema: Type[JobDocument]
    SampleResultsDocumentSchema: Type[SampleResultsDocument]
    JobResultsDocumentSchema: Type[JobResultsDocument]

    def __init__(
        self,
        host: str,
        root: str,
        key_path: Optional[str] = None,
        project_id: Optional[str] = None,
    ):
        super().__init__(
            host=host,
            root=root,
            key_path=key_path,
            project_id=project_id,
        )
        self.storage_client = StorageClient(
            key_path=key_path, project_id=self.project_id
        )
        self.firestore_client = FirestoreClient(
            key_path=key_path, project_id=self.project_id
        )

    def _get_resource(self, resource: str) -> str:
        return ResourcesOutput(
            **json.loads(
                self.call(
                    resource=resource,
                    verb="get",
                ).text
            )
        ).resource

    def _upload_sample_to_storage(
        self, sample: LocalSample, destination_bucket: str
    ) -> GSSample:
        gs_paths = []
        for local_path in sample.paths:
            blob_name = generate_file_id(file_path=local_path)

            self.storage_client.upload_blob(
                source_file_name=local_path,
                bucket_name=destination_bucket,
                blob_name=blob_name,
            )

            gs_paths.append(
                GSPath.from_bucket_and_blob_names(
                    bucket_name=destination_bucket, blob_name=blob_name
                )
            )

        return GSSample(paths=tuple(gs_paths))

    def _upload_samples_to_storage(
        self, samples: Iterable[LocalSample], destination_bucket: str
    ) -> List[GSSample]:
        return [
            self._upload_sample_to_storage(
                sample=sample, destination_bucket=destination_bucket
            )
            for sample in samples
        ]

    def _get_predictions(
        self,
        job_id: str,
        results_bucket_name: str,
        sample_id: str,
        wait_if_not_existing: bool,
        timeout: int,
        retry_wait_time: int = 60,
        total_waited_time: int = 0,
    ) -> SampleResultsDocument:
        raw_results = self.storage_client.download_blob(
            bucket_name=results_bucket_name,
            blob_name=make_results_blob_name(job_id=job_id, sample_id=sample_id),
            as_json=True,
        )

        if raw_results is not None:
            return self.SampleResultsDocumentSchema.model_validate(raw_results)

        if wait_if_not_existing is False:
            raise RuntimeError(
                f"No predictions found for job_id={job_id} and sample_id={sample_id}"
            )

        if total_waited_time + retry_wait_time > timeout:
            raise TimeoutError(
                f"Failed to retrieve predictions for job_id={job_id} "
                f"and asset_id={sample_id}, giving up after {timeout // 60} "
                f"minutes of trying"
            )

        time.sleep(retry_wait_time)
        total_waited_time += retry_wait_time

        return self._get_predictions(
            job_id=job_id,
            results_bucket_name=results_bucket_name,
            sample_id=sample_id,
            wait_if_not_existing=wait_if_not_existing,
            total_waited_time=total_waited_time,
            timeout=timeout,
            retry_wait_time=retry_wait_time,
        )

    def _chunk_predict(
        self,
        samples: List[LocalSample],
        resource: str,
        samples_bucket_name: str,
        input_kwargs: Optional[Dict[str, Any]],
        timeout: int,
    ) -> Output:
        gs_samples = self._upload_samples_to_storage(
            samples=samples, destination_bucket=samples_bucket_name
        )

        return self.OutputSchema(
            **json.loads(
                self.call(
                    resource=resource,
                    verb="post",
                    payload=self.InputSchema(samples=gs_samples, **input_kwargs).dict(),
                    timeout=timeout,
                ).text
            )
        )

    def _predict(
        self,
        samples: List[LocalSample],
        resource: str,
        samples_bucket_name: str,
        input_kwargs: Optional[Dict[str, Any]],
        timeout: int,
        maximum_elements_number: int,
    ) -> List[Output]:
        return [
            self._chunk_predict(
                samples=chunk_samples,
                resource=resource,
                samples_bucket_name=samples_bucket_name,
                input_kwargs=input_kwargs,
                timeout=timeout,
            )
            for chunk_samples in get_chunks_from_iterable(
                iterable=samples, chunk_size=maximum_elements_number
            )
        ]

    def _get_predictions_from_job_id(
        self,
        results_bucket_name: str,
        job_collection_name: str,
        job_id: str,
        wait_if_not_existing: bool = False,
        job_timeout: int = 2700,
    ) -> JobResultsDocument:
        raw_job_document = self.firestore_client.get_document(
            collection_name=job_collection_name,
            document_id=job_id,
        )

        if raw_job_document is None:
            raise PredictionsNotFoundError(f"No predictions found for job_id={job_id}")

        job_document = self.JobDocumentSchema.model_validate(raw_job_document)

        job_time_delta = max(
            (
                job_timeout
                - (datetime.datetime.utcnow() - job_document.job_date).seconds
            ),
            0,
        )

        try:
            return self.JobResultsDocumentSchema(
                results=[
                    self._get_predictions(
                        job_id=job_id,
                        results_bucket_name=results_bucket_name,
                        sample_id=sample_id,
                        wait_if_not_existing=wait_if_not_existing,
                        timeout=job_time_delta,
                    )
                    for sample_id in job_document.samples_ids
                ]
            )
        except TimeoutError as timeout_error:
            raise TimeoutError(
                f"At least one asset results could not be retrieved in time "
                f"(targeted job UTC date: {job_document.job_date})"
            ) from timeout_error

    def predict_async(
        self,
        samples: List[LocalSample],
        resource: str,
        samples_bucket_name: str,
        maximum_elements_number: int,
        input_kwargs: Optional[Dict[str, Any]] = None,
        timeout: int = 2700,
    ) -> List[Output]:
        return self._predict(
            samples=samples,
            resource=resource,
            samples_bucket_name=samples_bucket_name,
            input_kwargs=input_kwargs,
            timeout=timeout,
            maximum_elements_number=maximum_elements_number,
        )

    def predict_sync(
        self,
        samples: List[LocalSample],
        resource: str,
        samples_bucket_name: str,
        results_bucket_name: str,
        job_collection_name: str,
        maximum_elements_number: int,
        input_kwargs: Optional[Dict[str, Any]] = None,
        timeout: int = 60,
        job_timeout: int = 2700,
    ) -> List[SampleResultsDocument]:
        prediction_outputs = self._predict(
            samples=samples,
            resource=resource,
            samples_bucket_name=samples_bucket_name,
            input_kwargs=input_kwargs,
            timeout=timeout,
            maximum_elements_number=maximum_elements_number,
        )

        job_results = [
            self._get_predictions_from_job_id(
                results_bucket_name=results_bucket_name,
                job_collection_name=job_collection_name,
                job_id=prediction_output.job_id,
                wait_if_not_existing=True,
                job_timeout=job_timeout,
            )
            for prediction_output in prediction_outputs
        ]

        return [
            asset_results
            for job_result in job_results
            for asset_results in job_result.results
        ]

    def predict_real_time(
        self,
        sample: LocalSample,
        resource: str,
        samples_bucket_name: str,
        input_kwargs: Optional[Dict[str, Any]] = None,
        timeout: int = 2700,
    ) -> RealTimeOutput:
        gs_sample = self._upload_sample_to_storage(
            sample=sample,
            destination_bucket=samples_bucket_name,
        )

        return self.RealTimeOutputSchema(
            **json.loads(
                self.call(
                    resource=resource,
                    verb="post",
                    payload=self.RealTimeInputSchema(
                        sample=gs_sample, **input_kwargs
                    ).dict(),
                    timeout=timeout,
                ).text
            )
        )
