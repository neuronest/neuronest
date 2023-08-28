import os
import uuid
from typing import Optional

from core.google.cloud_run_job_manager import CloudRunJobManager
from core.google.storage_client import StorageClient
from core.path import GSPath
from core.routes.people_counting import routes
from core.schemas.google.cloud_run import JobConfig
from core.schemas.people_counting import (
    PeopleCounterInput,
    PeopleCounterOutput,
    PeopleCounterRealTimeOutput,
)
from core.services.asset_reader import make_asset_content
from core.tools import extract_file_extension
from fastapi import APIRouter, Depends, Response
from omegaconf import DictConfig
from starlette import status

from people_counting.api.dependencies import (
    use_cloud_run_job_manager,
    use_config,
    use_counted_videos_bucket,
    use_firestore_results_collection,
    use_people_counter,
    use_storage_client,
    use_videos_to_count_bucket,
)
from people_counting.common import Statistics
from people_counting.people_counter import PeopleCounter

resource_name = os.path.splitext(os.path.basename(__file__))[0]
router = APIRouter(prefix=f"/{resource_name}", tags=[resource_name])


def _launched_job_response(
    response: Response,
    job_id: str,
    asset_id: str,
    storage_path: GSPath,
    counted_video_storage_path: GSPath,
) -> PeopleCounterOutput:
    response.status_code = status.HTTP_201_CREATED

    return PeopleCounterOutput(
        job_id=job_id,
        asset_id=asset_id,
        storage_path=storage_path,
        counted_video_storage_path=counted_video_storage_path,
    )


def _real_time_response(
    response: Response, statistics: Statistics
) -> PeopleCounterRealTimeOutput:
    response.status_code = status.HTTP_200_OK

    return PeopleCounterRealTimeOutput(
        detections=statistics.to_detections(),
    )


def _validate_video_storage_path(video_storage_path: GSPath, expected_bucket_name: str):
    bucket_name, _ = GSPath(video_storage_path).to_bucket_and_blob_names()

    if bucket_name != expected_bucket_name:
        raise ValueError(
            f"Unexpected bucket name for storage path '{video_storage_path}', "
            f"expected {expected_bucket_name}, got {bucket_name}"
        )


def _maybe_create_counted_video_storage_path(
    job_id: str,
    asset_id: str,
    save_counted_video: bool,
    asset_path: str,
    counted_videos_bucket: str,
) -> Optional[GSPath]:
    if save_counted_video is False:
        return None

    extension = extract_file_extension(asset_path)
    counted_videos_blob_name = os.path.join(job_id, asset_id) + extension

    return GSPath.from_bucket_and_blob_names(
        bucket_name=counted_videos_bucket, blob_name=counted_videos_blob_name
    )


@router.post(
    routes.count_people,
    status_code=status.HTTP_201_CREATED,
)
def count_people(
    people_counter_input: PeopleCounterInput,
    response: Response,
    config: DictConfig = Depends(use_config),
    cloud_run_job_manager: CloudRunJobManager = Depends(use_cloud_run_job_manager),
    storage_client: StorageClient = Depends(use_storage_client),
    firestore_results_collection: str = Depends(use_firestore_results_collection),
    videos_to_count_bucket: str = Depends(use_videos_to_count_bucket),
    counted_videos_bucket: str = Depends(use_counted_videos_bucket),
) -> PeopleCounterOutput:
    job_id = uuid.uuid4().hex

    video_storage_path = people_counter_input.video_storage_path

    _validate_video_storage_path(
        video_storage_path=video_storage_path,
        expected_bucket_name=videos_to_count_bucket,
    )

    video_asset_content = make_asset_content(
        asset_path=people_counter_input.video_storage_path,
        storage_client=storage_client,
    )
    asset_id = video_asset_content.get_hash()

    counted_video_storage_path = _maybe_create_counted_video_storage_path(
        job_id=job_id,
        asset_id=asset_id,
        save_counted_video=people_counter_input.save_counted_video,
        asset_path=video_asset_content.asset_path,
        counted_videos_bucket=counted_videos_bucket,
    )

    job_name = f"count_people_{asset_id}"
    cloud_run_job_manager.create_job(
        job_name=job_name,
        job_config=JobConfig(
            container_uri=config.job.container_uri,
            cpu=config.job.cpu,
            memory=config.job.memory,
            command=["python"],
            command_args=[
                "-m",
                "people_counting.jobs.count_people",
            ],
            environment_variables={
                "JOB_ID": job_id,
                "ASSET_ID": asset_id,
                "VIDEO_STORAGE_PATH": people_counter_input.video_storage_path,
                "FIRESTORE_RESULTS_COLLECTION": firestore_results_collection,
                "COUNTED_VIDEO_STORAGE_PATH": counted_video_storage_path,
            },
        ),
        override_if_existing=True,
    )
    cloud_run_job_manager.run_job(job_name=job_name)

    return _launched_job_response(
        response=response,
        job_id=job_id,
        asset_id=asset_id,
        storage_path=people_counter_input.video_storage_path,
        counted_video_storage_path=counted_video_storage_path,
    )


# used for debugging purposes only
@router.post(
    routes.count_people_real_time_showing,
    status_code=status.HTTP_200_OK,
)
def count_people_real_time_showing(
    people_counter_input: PeopleCounterInput,
    response: Response,
    people_counter: PeopleCounter = Depends(use_people_counter),
    storage_client: StorageClient = Depends(use_storage_client),
    videos_to_count_bucket: str = Depends(use_videos_to_count_bucket),
) -> PeopleCounterRealTimeOutput:
    video_storage_path = people_counter_input.video_storage_path

    _validate_video_storage_path(
        video_storage_path=video_storage_path,
        expected_bucket_name=videos_to_count_bucket,
    )

    video_asset_content = make_asset_content(
        asset_path=people_counter_input.video_storage_path,
        storage_client=storage_client,
    )

    statistics = people_counter.run(
        video_asset_content=video_asset_content, enable_video_showing=True
    )

    return _real_time_response(response=response, statistics=statistics)
