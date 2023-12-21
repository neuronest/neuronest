from __future__ import annotations

import datetime
import json
import time
from typing import Iterable, List, Optional

from core.client.base import CloudRunBasedClient, HTTPClient
from core.exceptions import PredictionsNotFoundError
from core.google.firestore_client import FirestoreClient
from core.google.storage_client import StorageClient
from core.hashing import combine_hashes
from core.path import GSPath, LocalPath
from core.routes.people_counting import routes
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


def make_results_document_id(
    job_id: str,
    asset_id: str,
) -> str:
    return combine_hashes([job_id, asset_id])


class PeopleCountingClient(HTTPClient, CloudRunBasedClient):
    def __init__(
        self,
        host: str,
        key_path: Optional[str] = None,
        project_id: Optional[str] = None,
    ):
        super().__init__(
            host=host,
            key_path=key_path,
            root=routes.root,
            project_id=project_id,
        )
        self.storage_client = StorageClient(
            key_path=key_path, project_id=self.project_id
        )
        self.firestore_client = FirestoreClient(
            key_path=key_path, project_id=self.project_id
        )

    @classmethod
    def from_primitive_attributes(cls, **kwargs) -> PeopleCountingClient:
        mandatory_fields = ("host",)
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

    def _upload_video_to_storage(
        self, video_path: LocalPath, destination_bucket: str
    ) -> GSPath:
        video_blob_name = generate_file_id(file_path=video_path)

        self.storage_client.upload_blob(
            source_file_name=video_path,
            bucket_name=destination_bucket,
            blob_name=video_blob_name,
        )

        return GSPath.from_bucket_and_blob_names(
            bucket_name=destination_bucket, blob_name=video_blob_name
        )

    def _get_firestore_results_collection(self) -> str:
        return ResourcesOutput(
            **json.loads(
                self.call(
                    resource=f"/{routes.Resources.prefix}"
                    f"{routes.Resources.firestore_results_collection}",
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

    def _get_videos_to_count_bucket(self) -> str:
        return ResourcesOutput(
            **json.loads(
                self.call(
                    resource=f"/{routes.Resources.prefix}"
                    f"{routes.Resources.videos_to_count_bucket}",
                    verb="get",
                ).text
            )
        ).resource

    def _get_maximum_videos_number(self) -> int:
        return int(
            ResourcesOutput(
                **json.loads(
                    self.call(
                        resource=f"/{routes.Resources.prefix}"
                        f"{routes.Resources.maximum_videos_number}",
                        verb="get",
                    ).text
                )
            ).resource
        )

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
            collection_name=self._get_firestore_results_collection(),
            document_id=make_results_document_id(job_id=job_id, asset_id=asset_id),
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

    def _chunk_count_people(
        self,
        videos_paths: List[str],
        save_counted_videos_in_storage: bool,
    ) -> PeopleCounterOutput:
        uploaded_videos_storage_paths = [
            self._upload_video_to_storage(
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

    def _count_people(
        self,
        videos_paths: Iterable[str],
        save_counted_videos_in_storage: bool = False,
    ) -> List[PeopleCounterOutput]:
        return [
            self._chunk_count_people(
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

    def count_people_async(
        self,
        videos_paths: List[str],
        save_counted_videos_in_storage: bool = False,
    ) -> List[PeopleCounterOutput]:
        return self._count_people(
            videos_paths=videos_paths,
            save_counted_videos_in_storage=save_counted_videos_in_storage,
        )

    def count_people_sync(
        self,
        videos_paths: Iterable[str],
        save_counted_videos_in_storage: bool = False,
    ) -> List[PeopleCounterAssetResultsDocument]:
        people_counter_outputs = self._count_people(
            videos_paths=videos_paths,
            save_counted_videos_in_storage=save_counted_videos_in_storage,
        )

        people_counter_job_results_documents = [
            self.get_predictions_from_job_id(
                job_id=people_counter_output.job_id, wait_if_not_existing=True
            )
            for people_counter_output in people_counter_outputs
        ]

        return [
            asset_results
            for people_counter_job_results_document in (
                people_counter_job_results_documents
            )
            for asset_results in people_counter_job_results_document.results
        ]

    # used for debugging purposes only
    def count_people_real_time(
        self,
        video_path: str,
        save_counted_video_in_storage: bool = False,
        enable_video_showing: bool = False,
        timeout: int = 2700,
    ) -> PeopleCounterRealTimeOutput:
        uploaded_video_storage_path = self._upload_video_to_storage(
            video_path=LocalPath(video_path),
            destination_bucket=self._get_videos_to_count_bucket(),
        )

        return PeopleCounterRealTimeOutput(
            **json.loads(
                self.call(
                    resource=f"/{routes.PeopleCounter.prefix}"
                    f"{routes.PeopleCounter.count_people_real_time}",
                    verb="post",
                    payload=PeopleCounterRealTimeInput(
                        video_storage_path=uploaded_video_storage_path,
                        save_counted_video=save_counted_video_in_storage,
                        enable_video_showing=enable_video_showing,
                    ).dict(),
                    timeout=timeout,
                ).text
            )
        )
