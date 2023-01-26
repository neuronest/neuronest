import logging
import os

from api import dependencies
from api.crud import counter
from api.model.result import JobResult
from api.model.video_message import VideoMessage
from fastapi import APIRouter, Body, Depends
from google.cloud import firestore  # pylint: disable=no-name-in-module
from google.cloud import storage
from people_counting.people_counter import PeopleCounter

router = APIRouter()

logger = logging.getLogger(__name__)


@router.post("/count_people_and_make_video")
def count_people_and_make_video(
    *,
    video_to_count_message: VideoMessage = Body(..., embed=False),
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
) -> JobResult:
    video_to_count_local_path = os.path.basename(
        video_to_count_message.data.storage_path
    )
    bucket_of_videos_to_count.blob(
        video_to_count_message.data.storage_path
    ).download_to_filename(video_to_count_local_path)
    people_counting, counted_video_local_path = counter.count_people(
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
    result = JobResult(
        **people_counting.dict(), counted_video_storage_path=counted_video_storage_path
    )
    results_collection.document(video_to_count_message.data.job_id).set(result.dict())
    return result
