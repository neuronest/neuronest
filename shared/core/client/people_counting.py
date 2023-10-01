import json
from typing import Optional

from core.client.base import APIClient
from core.google.storage_client import StorageClient
from core.path import GSPath, LocalPath
from core.routes.people_counting import routes
from core.schemas.people_counting import (
    PeopleCounterInput,
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

    def get_videos_to_count_bucket(self) -> str:
        return VideosToCountBucketOutput(
            **json.loads(
                self.call(
                    resource=f"/{routes.PeopleCounter.prefix}"
                    f"{routes.PeopleCounter.videos_to_count_bucket}",
                    verb="get",
                ).text
            )
        ).bucket

    def count_people_real_time(
        self, video_path: str, save_counted_video_in_storage: bool = False
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
                ).text
            )
        )
