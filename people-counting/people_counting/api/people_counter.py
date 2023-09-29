import os
from typing import Tuple

from core.routes.people_counting import routes
from core.schemas import people_counting as schemas
from core.tools import maybe_async
from fastapi import APIRouter, Body, Depends
from google.cloud import firestore, storage
from starlette import status

from people_counting.api import dependencies
from people_counting.common import Statistics
from people_counting.config import config
from people_counting.people_counter import PeopleCounter

router = APIRouter(
    prefix=f"/{routes.PeopleCounter.prefix}", tags=[routes.PeopleCounter.prefix]
)


def count_people_and_make_video_from_local_path(
    people_counter: PeopleCounter,
    video_path: str,
    write_video: bool = False,
    enable_video_showing: bool = False,
) -> Tuple[Statistics, str]:
    counting_statistics, video_renderer = people_counter.run(
        video_path,
        enable_video_writing=write_video,
        enable_video_showing=enable_video_showing,
    )
    counted_video_path = video_renderer.output_path if write_video else None

    return counting_statistics, counted_video_path


# if we want to show the video in case of debug we make the function async
# so that fastapi does not place the path operation function in a thread,
# which is a problem when showing the video
@router.post(
    routes.PeopleCounter.count_people_and_make_video,
    status_code=status.HTTP_201_CREATED,
)
@maybe_async(config.general.enable_video_showing)
def count_people_and_make_video(
    *,
    input_of_people_counter: schemas.PeopleCounterInput = Body(..., embed=False),
    people_counter: PeopleCounter = Depends(dependencies.get_people_counter),
    collection_of_people_counter_output: firestore.CollectionReference = Depends(
        dependencies.get_firestore_results_collection
    ),
    bucket_of_videos_to_count: storage.Bucket = Depends(
        dependencies.get_bucket_of_videos_to_count
    ),
    bucket_of_counted_videos: storage.Bucket = Depends(
        dependencies.get_bucket_of_counted_videos
    ),
) -> schemas.PeopleCounterOutput:
    video_to_count_local_path = os.path.basename(
        input_of_people_counter.data.storage_path
    )
    blob_name = "/".join(
        input_of_people_counter.data.storage_path.lstrip("gs://").split("/")[1:]
    )
    bucket_of_videos_to_count.blob(blob_name).download_to_filename(
        video_to_count_local_path
    )
    (
        counting_statistics,
        counted_video_local_path,
    ) = count_people_and_make_video_from_local_path(
        people_counter=people_counter,
        video_path=video_to_count_local_path,
        write_video=input_of_people_counter.data.save_counted_video_in_storage,
        enable_video_showing=input_of_people_counter.data.enable_video_showing,
    )
    if input_of_people_counter.data.save_counted_video_in_storage:
        counted_video_storage_path = os.path.basename(video_to_count_local_path)
        bucket_of_counted_videos.blob(counted_video_storage_path).upload_from_filename(
            counted_video_local_path
        )
    else:
        counted_video_storage_path = None
    people_counter_output = schemas.PeopleCounterOutput(
        detections=[
            schemas.Detection(timestamp=timestamp, direction=direction)
            for timestamp, direction in zip(
                counting_statistics.timestamps,
                counting_statistics.passed_people_directions,
            )
        ],
        counted_video_storage_path=counted_video_storage_path,
    )
    collection_of_people_counter_output.document(
        input_of_people_counter.data.job_id
    ).set(people_counter_output.dict())

    return people_counter_output
