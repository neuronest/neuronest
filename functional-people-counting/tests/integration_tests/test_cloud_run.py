import os
import tempfile
from typing import List, Optional

import pytest
from core.client.people_counting import PeopleCountingClient
from core.google.storage_client import StorageClient
from core.path import GSPath
from core.schemas.people_counting import Detection, Direction


def are_detections_correct(
    detections: List[Detection], up_amount: int, down_amount: int
) -> bool:
    return up_amount == sum(
        detection.direction == Direction.UP for detection in detections
    ) and down_amount == sum(
        detection.direction == Direction.DOWN for detection in detections
    )


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
    google_application_credentials: Optional[str],
):
    people_counting_client = PeopleCountingClient(
        host=people_counting_url, project_id=project_id
    )

    video_bucket, video_blob_name = video_storage_path.to_bucket_and_blob_names()
    _, extension = os.path.splitext(video_blob_name)

    with tempfile.NamedTemporaryFile(suffix=extension) as named_temporary_file:
        StorageClient(key_path=google_application_credentials).download_blob_to_file(
            bucket_name=video_bucket,
            source_blob_name=video_blob_name,
            destination_file_name=named_temporary_file.name,
        )

        people_counter_output = people_counting_client.count_people(
            video_path=named_temporary_file.name
        )
        people_counter_document = (
            people_counting_client.retrieve_counted_people_document(
                job_id=people_counter_output.job_id, wait_if_not_existing=True
            )
        )

        assert people_counter_document.job_id == people_counter_output.job_id
        assert are_detections_correct(
            detections=people_counter_document.detections,
            up_amount=up_amount,
            down_amount=down_amount,
        )

        real_time_predictions = people_counting_client.count_people_real_time(
            video_path=named_temporary_file.name
        )
        assert are_detections_correct(
            detections=real_time_predictions.detections,
            up_amount=up_amount,
            down_amount=down_amount,
        )
