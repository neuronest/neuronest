import os
import tempfile

import pytest
from core.client.people_counting import PeopleCountingClient
from core.google.storage_client import StorageClient
from core.path import GSPath
from core.schemas.people_counting import Direction


@pytest.mark.parametrize(
    "video_storage_path, up_amount, down_amount",
    [
        (
            GSPath(
                "gs://datasets-neuronest/on_off_bus_videos"
                "/301_20150512_front_normal_uncrowd_2015_05_12_11_09_40FrontColor.avi"
            ),
            0,
            4,
        )
    ],
)
def test_cloud_run_inference(
    people_counting_url: str,
    project_id: str,
    video_storage_path: GSPath,
    up_amount: int,
    down_amount: int,
):
    people_counting_client = PeopleCountingClient(
        host=people_counting_url, project_id=project_id
    )

    video_bucket, video_blob_name = video_storage_path.to_bucket_and_blob_names()
    _, extension = os.path.splitext(video_blob_name)

    with tempfile.NamedTemporaryFile(suffix=extension) as named_temporary_file:
        StorageClient().download_blob_to_file(
            bucket_name=video_bucket,
            source_blob_name=video_blob_name,
            destination_file_name=named_temporary_file.name,
        )

        prediction = people_counting_client.count_people_real_time(
            video_path=named_temporary_file.name
        )

        assert up_amount == sum(
            detection.direction == Direction.UP for detection in prediction.detections
        )
        assert down_amount == sum(
            detection.direction == Direction.DOWN for detection in prediction.detections
        )
