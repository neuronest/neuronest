import logging
import os
from typing import Tuple

from core.schemas import people_counting as people_counting_schemas
from fastapi import APIRouter, Body, Depends
from google.cloud import firestore  # pylint: disable=no-name-in-module
from google.cloud import storage
from people_counting.api import dependencies
from people_counting.common import Statistics
from people_counting.people_counter import PeopleCounter

router = APIRouter()

logger = logging.getLogger(__name__)


def count_people_and_make_video_from_local_path(
    people_counter: PeopleCounter, video_path: str, write_video: bool = False
) -> Tuple[Statistics, str]:
    counting_statistics, video_renderer = people_counter.run(
        video_path, enable_video_writing=write_video, enable_video_showing=False
    )
    counted_video_path = video_renderer.output_path if write_video else None
    return (
        counting_statistics,
        # PeopleCounting.from_counting_statistics(counting_statistics=counting_statistics),
        counted_video_path,
    )


@router.post("/count_people_and_make_video")
def count_people_and_make_video(
    *,
    video_to_count_message: people_counting_schemas.PeopleCounterInput = Body(
        ..., embed=False
    ),
    people_counter: PeopleCounter = Depends(dependencies.get_people_counter),
    results_collection: firestore.CollectionReference = Depends(
        dependencies.get_firestore_results_collection
    ),
    bucket_of_videos_to_count: storage.Bucket = Depends(
        dependencies.get_bucket_of_videos_to_count
    ),
    bucket_of_counted_videos: storage.Bucket = Depends(
        dependencies.get_bucket_of_counted_videos
    ),
) -> people_counting_schemas.PeopleCounterOutput:
    video_to_count_local_path = os.path.basename(
        video_to_count_message.data.storage_path
    )
    bucket_of_videos_to_count.blob(
        video_to_count_message.data.storage_path
    ).download_to_filename(video_to_count_local_path)
    (
        counting_statistics,
        counted_video_local_path,
    ) = count_people_and_make_video_from_local_path(
        people_counter=people_counter,
        video_path=video_to_count_local_path,
        write_video=video_to_count_message.data.save_counted_video_in_storage,
    )
    if video_to_count_message.data.save_counted_video_in_storage:
        counted_video_storage_path = os.path.basename(video_to_count_local_path)
        bucket_of_counted_videos.blob(counted_video_storage_path).upload_from_filename(
            counted_video_local_path
        )
    else:
        counted_video_storage_path = None
    people_counter_output = people_counting_schemas.PeopleCounterOutput(
        detections=[
            people_counting_schemas.Detection(timestamp=timestamp, direction=direction)
            for timestamp, direction in zip(
                counting_statistics.timestamps,
                counting_statistics.passed_people_directions,
            )
        ],
        counted_video_storage_path=counted_video_storage_path,
    )
    results_collection.document(video_to_count_message.data.job_id).set(
        people_counter_output.dict()
    )
    return people_counter_output
