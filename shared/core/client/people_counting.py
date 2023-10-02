import json
import time
from typing import Optional

from core.client.base import APIClient
from core.google.firestore_client import FirestoreClient
from core.google.storage_client import StorageClient
from core.path import GSPath, LocalPath
from core.routes.people_counting import routes
from core.schemas.people_counting import (
    FirestoreResultsCollectionOutput,
    PeopleCounterDocument,
    PeopleCounterInput,
    PeopleCounterOutput,
    PeopleCounterRealTimeOutput,
    VideosToCountBucketOutput,
)
from core.tools import generate_file_id


class PeopleCountingClient(APIClient):
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

    def get_firestore_results_collection(self) -> str:
        return FirestoreResultsCollectionOutput(
            **json.loads(
                self.call(
                    resource=f"/{routes.Resources.prefix}"
                    f"{routes.Resources.firestore_results_collection}",
                    verb="get",
                ).text
            )
        ).collection

    def get_videos_to_count_bucket(self) -> str:
        return VideosToCountBucketOutput(
            **json.loads(
                self.call(
                    resource=f"/{routes.Resources.prefix}"
                    f"{routes.Resources.videos_to_count_bucket}",
                    verb="get",
                ).text
            )
        ).bucket

    def retrieve_counted_people_document(
        self,
        job_id: str,
        wait_if_not_existing: bool = False,
        total_waited_time: int = 0,
        timeout: int = 2700,
        retry_wait_time: int = 60,
    ) -> PeopleCounterDocument:
        raw_document = self.firestore_client.get_document(
            collection_name=self.get_firestore_results_collection(),
            document_id=job_id,
        )

        if raw_document is None and wait_if_not_existing is False:
            raise RuntimeError(f"Document not found for job_id={job_id}")

        if raw_document is None:
            time.sleep(retry_wait_time)
            total_waited_time += retry_wait_time

            if total_waited_time > timeout:
                raise TimeoutError(
                    f"Failed to retrieve document having job_id={job_id}, "
                    f"giving up after {timeout // 60} minutes of trying"
                )

            return self.retrieve_counted_people_document(
                job_id=job_id,
                wait_if_not_existing=wait_if_not_existing,
                total_waited_time=total_waited_time,
                timeout=timeout,
                retry_wait_time=retry_wait_time,
            )

        return PeopleCounterDocument.parse_obj(raw_document)

    def count_people(
        self,
        video_path: str,
        save_counted_video_in_storage: bool = False,
    ) -> PeopleCounterOutput:
        uploaded_video_storage_path = self._upload_video_to_storage(
            video_path=LocalPath(video_path),
            destination_bucket=self.get_videos_to_count_bucket(),
        )

        return PeopleCounterOutput(
            **json.loads(
                self.call(
                    resource=f"/{routes.PeopleCounter.prefix}"
                    f"{routes.PeopleCounter.count_people}",
                    verb="post",
                    payload=PeopleCounterInput(
                        video_storage_path=uploaded_video_storage_path,
                        save_counted_video_in_storage=save_counted_video_in_storage,
                    ).dict(),
                ).text
            )
        )

    def count_people_real_time(
        self,
        video_path: str,
        save_counted_video_in_storage: bool = False,
        timeout: int = 2700,
    ) -> PeopleCounterRealTimeOutput:
        uploaded_video_storage_path = self._upload_video_to_storage(
            video_path=LocalPath(video_path),
            destination_bucket=self.get_videos_to_count_bucket(),
        )

        return PeopleCounterRealTimeOutput(
            **json.loads(
                self.call(
                    resource=f"/{routes.PeopleCounter.prefix}"
                    f"{routes.PeopleCounter.count_people_real_time}",
                    verb="post",
                    payload=PeopleCounterInput(
                        video_storage_path=uploaded_video_storage_path,
                        save_counted_video_in_storage=save_counted_video_in_storage,
                    ).dict(),
                    timeout=timeout,
                ).text
            )
        )
