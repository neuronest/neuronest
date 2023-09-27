import datetime
import json
import uuid
from typing import Optional

from core.client.base import APIClient
from core.google.storage_client import StorageClient
from core.path import GSPath
from core.routes.people_counting import routes
from core.schemas.people_counting import (
    PeopleCounterInput,
    PeopleCounterInputData,
    PeopleCounterOutput,
)
from core.tools import generate_file_id


class PeopleCountingClient(APIClient):
    VIDEOS_TO_COUNT_BASE_BUCKET_NAME = "pc-videos-to-count"
    PREDICTION_INSTANCE_ID_DATETIME_FORMAT = "%Y_%m_%d_%H:%M:%S"

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

    @property
    def videos_to_count_bucket(self) -> str:
        return f"{self.VIDEOS_TO_COUNT_BASE_BUCKET_NAME}-{self.project_id}"

    def _upload_video_to_storage(self, video_path: str) -> GSPath:
        bucket = self.storage_client.client.bucket(self.videos_to_count_bucket)

        if not bucket.exists():
            bucket.create()

        video_blob_name = generate_file_id(file_path=video_path)

        self.storage_client.upload_blob(
            source_file_name=video_path,
            bucket_name=bucket.name,
            blob_name=video_blob_name,
        )

        return GSPath.from_bucket_and_blob_names(
            bucket_name=bucket.name, blob_name=video_blob_name
        )

    def get_prediction_instance_id(self, video_path: str):
        now = datetime.datetime.now().strftime(
            self.PREDICTION_INSTANCE_ID_DATETIME_FORMAT
        )
        return f"{now}_{generate_file_id(file_path=video_path)}_{str(uuid.uuid4())}"

    def predict(
        self, video_path: str, save_counted_video_in_storage: bool = False
    ) -> PeopleCounterOutput:
        uploaded_video_storage_path = self._upload_video_to_storage(
            video_path=video_path
        )

        return PeopleCounterOutput(
            **json.loads(
                self.call(
                    resource=f"/{routes.PeopleCounter.prefix}"
                    f"{routes.PeopleCounter.count_people_and_make_video}",
                    verb="post",
                    payload=PeopleCounterInput(
                        data=PeopleCounterInputData(
                            job_id=self.get_prediction_instance_id(
                                video_path=video_path
                            ),
                            storage_path=uploaded_video_storage_path,
                            save_counted_video_in_storage=save_counted_video_in_storage,
                            enable_video_showing=False,
                        )
                    ).dict(),
                ).text
            )
        )
