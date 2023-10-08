import os
import tempfile
from typing import List

import pytest
from core.client.model_instantiator import ModelInstantiatorClient
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


@pytest.fixture(name="uninstantiate_teardown", autouse=True)
def fixture_uninstantiate_teardown(
    model_instantiator_client: ModelInstantiatorClient,
    model_name: str,
):
    try:
        yield
    finally:
        model_instantiator_client.uninstantiate(model_name=model_name)


@pytest.mark.parametrize(
    "videos_storage_paths, up_amounts, down_amounts",
    [
        (
            [
                GSPath("gs://datasets-neuronest/on_off_bus_videos/example_up.mp4"),
                GSPath("gs://datasets-neuronest/on_off_bus_videos/example_down.avi"),
            ],
            [4, 0],
            [0, 4],
        )
    ],
)
# pylint: disable=too-many-locals
def test_cloud_run_inference(
    people_counting_client: PeopleCountingClient,
    storage_client: StorageClient,
    videos_storage_paths: List[GSPath],
    up_amounts: List[int],
    down_amounts: List[int],
):
    videos_buckets, videos_blob_names = list(
        zip(
            *[
                video_storage_path.to_bucket_and_blob_names()
                for video_storage_path in videos_storage_paths
            ]
        )
    )
    extensions = [
        os.path.splitext(video_blob_name)[1] for video_blob_name in videos_blob_names
    ]

    with tempfile.TemporaryDirectory() as temporary_directory:
        temporary_videos_paths = []
        for index, (video_bucket, video_blob_name, extension) in enumerate(
            zip(videos_buckets, videos_blob_names, extensions)
        ):
            temporary_video_path = os.path.join(
                temporary_directory, str(index) + extension
            )
            storage_client.download_blob_to_file(
                bucket_name=video_bucket,
                source_blob_name=video_blob_name,
                destination_file_name=temporary_video_path,
            )
            temporary_videos_paths.append(temporary_video_path)

        people_counter_output = people_counting_client.count_people(
            videos_paths=temporary_videos_paths,
        )
        people_counter_job_results_document = (
            people_counting_client.get_predictions_from_job_id(
                job_id=people_counter_output.job_id, wait_if_not_existing=True
            )
        )

        assert all(
            people_counter_asset_results_document.job_id == people_counter_output.job_id
            for people_counter_asset_results_document in (
                people_counter_job_results_document.results
            )
        )
        assert all(
            are_detections_correct(
                detections=people_counter_asset_results_document.detections,
                up_amount=up_amount,
                down_amount=down_amount,
            )
            for people_counter_asset_results_document, up_amount, down_amount in zip(
                people_counter_job_results_document.results, up_amounts, down_amounts
            )
        )

        multiple_real_time_predictions = [
            people_counting_client.count_people_real_time(
                video_path=temporary_video_path
            )
            for temporary_video_path in temporary_videos_paths
        ]
        assert all(
            are_detections_correct(
                detections=real_time_predictions.detections,
                up_amount=up_amount,
                down_amount=down_amount,
            )
            for real_time_predictions, up_amount, down_amount in zip(
                multiple_real_time_predictions, up_amounts, down_amounts
            )
        )
