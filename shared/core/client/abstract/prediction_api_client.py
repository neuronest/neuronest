import datetime
import json
import time
from abc import ABC
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel

from core.client.abstract.api_client import APIClient
from core.exceptions import PredictionsNotFoundError
from core.google.firestore_client import FirestoreClient
from core.google.storage_client import StorageClient
from core.hashing import combine_hashes
from core.path import GSPath, LocalPath
from core.routes.video_comparator import routes
from core.schemas.abstract.prediction_api_client import RealTimeInput, RealTimeOutput
from core.schemas.people_counting import (
    PeopleCounterAssetResultsDocument,
    PeopleCounterInput,
    PeopleCounterJobDocument,
    PeopleCounterJobResultsDocument,
    PeopleCounterOutput,
    PeopleCounterRealTimeInput,
    PeopleCounterRealTimeOutput,
    ResourcesOutput,
)
from core.tools import generate_file_id, get_chunks_from_iterable


class PredictionAPIClient(APIClient, ABC):
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

    @staticmethod
    def _make_results_document_id(
        job_id: str,
        asset_id: str,
    ) -> str:
        return combine_hashes([job_id, asset_id])

    def _upload_object_to_storage(
        self, object_path: LocalPath, destination_bucket: str
    ) -> GSPath:
        blob_name = generate_file_id(file_path=object_path)

        self.storage_client.upload_blob(
            source_file_name=object_path,
            bucket_name=destination_bucket,
            blob_name=blob_name,
        )

        return GSPath.from_bucket_and_blob_names(
            bucket_name=destination_bucket, blob_name=blob_name
        )

    def _get_elements_to_predict_bucket(self) -> str:
        return ResourcesOutput(
            **json.loads(
                self.call(
                    resource=f"/{routes.Resources.prefix}"
                    f"{routes.Resources.elements_to_predict_bucket}",
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

    def _get_predictions(
        self,
        job_id: str,
        asset_id: str,
        wait_if_not_existing: bool,
        timeout: int,
        retry_wait_time: int = 60,
        total_waited_time: int = 0,
    ) -> PeopleCounterAssetResultsDocument:
        results_document = self.firestore_client.get_document(
            collection_name=self._get_job_results_bucket(),
            document_id=self._make_results_document_id(
                job_id=job_id, asset_id=asset_id
            ),
        )

        if results_document is not None:
            return PeopleCounterAssetResultsDocument.parse_obj(results_document)

        if wait_if_not_existing is False:
            raise RuntimeError(
                f"No predictions found for job_id={job_id} and asset_id={asset_id}"
            )

        if total_waited_time + retry_wait_time > timeout:
            raise TimeoutError(
                f"Failed to retrieve predictions for job_id={job_id} "
                f"and asset_id={asset_id}, giving up after {timeout // 60} "
                f"minutes of trying"
            )

        time.sleep(retry_wait_time)
        total_waited_time += retry_wait_time

        return self._get_predictions(
            job_id=job_id,
            asset_id=asset_id,
            wait_if_not_existing=wait_if_not_existing,
            total_waited_time=total_waited_time,
            timeout=timeout,
            retry_wait_time=retry_wait_time,
        )

    def _chunk_predict(
        self,
        videos_paths: List[str],
        save_counted_videos_in_storage: bool,
    ) -> PeopleCounterOutput:
        uploaded_videos_storage_paths = [
            upload_object_to_storage(
                storage_client=self.storage_client,
                video_path=LocalPath(video_path),
                destination_bucket=self._get_videos_to_count_bucket(),
            )
            for video_path in videos_paths
        ]

        return PeopleCounterOutput(
            **json.loads(
                self.call(
                    resource=f"/{routes.PeopleCounter.prefix}"
                    f"{routes.PeopleCounter.count_people}",
                    verb="post",
                    payload=PeopleCounterInput(
                        videos_storage_paths=uploaded_videos_storage_paths,
                        save_counted_videos=save_counted_videos_in_storage,
                    ).dict(),
                ).text
            )
        )

    def _predict(
        self,
        videos_paths: List[str],
        save_counted_videos_in_storage: bool = False,
    ) -> List[PeopleCounterOutput]:
        return [
            self._chunk_predict(
                videos_paths=chunk_videos_paths,
                save_counted_videos_in_storage=save_counted_videos_in_storage,
            )
            for chunk_videos_paths in get_chunks_from_iterable(
                iterable=videos_paths, chunk_size=self._get_maximum_videos_number()
            )
        ]

    def get_predictions_from_job_id(
        self,
        job_id: str,
        wait_if_not_existing: bool = False,
        job_timeout: int = 2700,
    ) -> PeopleCounterJobResultsDocument:
        raw_job_document = self.firestore_client.get_document(
            collection_name=self._get_firestore_jobs_collection(),
            document_id=job_id,
        )

        if raw_job_document is None:
            raise PredictionsNotFoundError(f"No predictions found for job_id={job_id}")

        job_document = PeopleCounterJobDocument.parse_obj(raw_job_document)
        job_time_delta = max(
            (
                job_timeout
                - (datetime.datetime.utcnow() - job_document.job_date).seconds
            ),
            0,
        )

        try:
            return PeopleCounterJobResultsDocument(
                results=[
                    self._get_predictions(
                        job_id=job_id,
                        asset_id=asset_id,
                        wait_if_not_existing=wait_if_not_existing,
                        timeout=job_time_delta,
                    )
                    for asset_id in job_document.assets_ids
                ]
            )
        except TimeoutError as timeout_error:
            raise TimeoutError(
                f"At least one asset results could not be retrieved in time "
                f"(targeted job UTC date: {job_document.job_date})"
            ) from timeout_error

    def predict_async(
        self,
        videos_paths: List[str],
        save_counted_videos_in_storage: bool = False,
    ) -> List[PeopleCounterOutput]:
        return self._predict(
            videos_paths=videos_paths,
            save_counted_videos_in_storage=save_counted_videos_in_storage,
        )

    def predict_sync(
        self,
        elements_paths: List[LocalPath],
        input_kwargs: Optional[Dict[str, Any]] = None,
    ) -> List[PeopleCounterAssetResultsDocument]:
        prediction_outputs = self._predict(
            elements_paths=elements_paths,
            input_kwargs=input_kwargs,
        )

        job_results = [
            self.get_predictions_from_job_id(
                job_id=people_counter_output.job_id, wait_if_not_existing=True
            )
            for prediction_output in prediction_outputs
        ]

        return [
            asset_results
            for people_counter_job_results_document in (
                people_counter_job_results_documents
            )
            for asset_results in people_counter_job_results_document.results
        ]

    def predict_real_time(
        self,
        element_path: LocalPath,
        resource: str,
        input_class: Type[RealTimeInput],
        output_class: Type[RealTimeOutput],
        input_kwargs: Optional[Dict[str, Any]] = None,
        timeout: int = 2700,
    ) -> RealTimeOutput:
        uploaded_video_storage_path = self._upload_object_to_storage(
            object_path=element_path,
            destination_bucket=self._get_elements_to_predict_bucket(),
        )

        return output_class(
            **json.loads(
                self.call(
                    resource=resource,
                    verb="post",
                    payload=input_class(
                        element_storage_path=uploaded_video_storage_path, **input_kwargs
                    ).dict(),
                    timeout=timeout,
                ).text
            )
        )
