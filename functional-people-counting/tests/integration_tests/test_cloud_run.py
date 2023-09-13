import os

import pytest
from core.client.people_counting import PeopleCountingClient
from core.google.storage_client import StorageClient
from core.path import GSPath
from core.schemas.people_counting import Direction


@pytest.mark.parametrize(
    "video_storage_path, up_amount, down_amount",
    [
        (
            "gs://datasets-neuronest/on_off_bus_videos"
            "/301_20150512_front_normal_uncrowd_2015_05_12_11_09_40FrontColor.avi",
            0,
            4,
        )
    ],
)
def test_cloud_run_inference(
    people_counting_url: str,
    project_id: str,
    video_storage_path: str,
    up_amount: int,
    down_amount: int,
):
    people_counting_client = PeopleCountingClient(
        host=people_counting_url, project_id=project_id
    )

    video_storage_bucket, video_storage_blob_name = GSPath(
        video_storage_path
    ).to_bucket_and_blob_names()

    StorageClient().download_blob_to_file(
        bucket_name=video_storage_bucket,
        source_blob_name=video_storage_blob_name,
        destination_file_name=os.path.basename(video_storage_path),
    )

    prediction = people_counting_client.predict(os.path.basename(video_storage_path))

    assert up_amount == sum(
        detection.direction == Direction.UP for detection in prediction.detections
    )
    assert down_amount == sum(
        detection.direction == Direction.DOWN for detection in prediction.detections
    )

    os.remove(os.path.basename(video_storage_path))
