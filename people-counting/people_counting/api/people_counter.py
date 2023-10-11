import os
import uuid
from datetime import datetime
from typing import List, Optional

from core.api_exceptions import abort
from core.google.cloud_run_job_manager import CloudRunJobManager
from core.google.firestore_client import FirestoreClient
from core.google.storage_client import StorageClient
from core.path import GSPath
from core.routes.people_counting import routes
from core.schemas.asset import AssetType
from core.schemas.google.cloud_run import JobConfig
from core.schemas.people_counting import (
    PeopleCounterInput,
    PeopleCounterJobDocument,
    PeopleCounterOutput,
    PeopleCounterRealTimeInput,
    PeopleCounterRealTimeOutput,
)
from core.services.asset_reader import make_asset, make_assets
from core.tools import extract_file_extension
from fastapi import APIRouter, Depends, Response
from omegaconf import DictConfig
from starlette import status

from people_counting.api.dependencies import (
    use_cloud_run_job_manager,
    use_config,
    use_firestore_client,
    use_firestore_jobs_collection,
    use_people_counter,
    use_storage_client,
)
from people_counting.common import Statistics
from people_counting.environment_variables import (
    COUNTED_VIDEOS_BUCKET,
    FIRESTORE_RESULTS_COLLECTION,
    MODEL_INSTANTIATOR_HOST,
    OBJECT_DETECTION_MODEL_NAME,
    PROJECT_ID,
    REGION,
    VIDEOS_TO_COUNT_BUCKET,
)
from people_counting.people_counter import PeopleCounter, count_people_with_upload

router = APIRouter(
    prefix=f"/{routes.PeopleCounter.prefix}", tags=[routes.PeopleCounter.prefix]
)


def _launched_job_response(
    response: Response,
    job_id: str,
) -> PeopleCounterOutput:
    response.status_code = status.HTTP_201_CREATED

    return PeopleCounterOutput(
        job_id=job_id,
    )


def _real_time_response(
    response: Response,
    statistics: Statistics,
    counted_video_storage_path: Optional[GSPath],
) -> PeopleCounterRealTimeOutput:
    response.status_code = status.HTTP_200_OK

    return PeopleCounterRealTimeOutput(
        detections=statistics.to_detections(),
        counted_video_storage_path=counted_video_storage_path,
    )


def _validate_video_storage_path(video_storage_path: GSPath, expected_bucket_name: str):
    bucket_name, _ = GSPath(video_storage_path).to_bucket_and_blob_names()

    if bucket_name != expected_bucket_name:
        raise ValueError(
            f"Unexpected bucket name for storage path '{video_storage_path}', "
            f"expected {expected_bucket_name}, got {bucket_name}"
        )


def _validate_video_storage_paths(
    videos_storage_paths: List[GSPath], expected_bucket_name: str
):
    for video_storage_path in videos_storage_paths:
        _validate_video_storage_path(
            video_storage_path=video_storage_path,
            expected_bucket_name=expected_bucket_name,
        )


def _create_counted_video_storage_path(
    asset_id: str,
    asset_path: str,
    counted_videos_bucket: str,
    job_id: Optional[str] = None,
) -> Optional[GSPath]:
    extension = extract_file_extension(asset_path)

    if job_id is None:
        counted_videos_blob_name = asset_id + extension
    else:
        counted_videos_blob_name = os.path.join(asset_id, job_id) + extension

    return GSPath.from_bucket_and_blob_names(
        bucket_name=counted_videos_bucket, blob_name=counted_videos_blob_name
    )


def _upload_people_job_document(
    firestore_client: FirestoreClient,
    firestore_jobs_collection: str,
    job_id: str,
    assets_ids: List[str],
):
    people_job_document = PeopleCounterJobDocument(
        job_id=job_id, job_date=datetime.now(), assets_ids=assets_ids
    )
    firestore_client.upload_document(
        collection_name=firestore_jobs_collection,
        document_id=job_id,
        content=people_job_document.dict(),
    )


@router.post(
    routes.PeopleCounter.count_people,
    status_code=status.HTTP_201_CREATED,
)
def count_people(
    people_counter_input: PeopleCounterInput,
    response: Response,
    config: DictConfig = Depends(use_config),
    cloud_run_job_manager: CloudRunJobManager = Depends(use_cloud_run_job_manager),
    storage_client: StorageClient = Depends(use_storage_client),
    firestore_client: FirestoreClient = Depends(use_firestore_client),
    firestore_jobs_collection: str = Depends(use_firestore_jobs_collection),
) -> PeopleCounterOutput:
    job_id = uuid.uuid4().hex

    if (
        len(people_counter_input.videos_storage_paths)
        > config.api.maximum_videos_number
    ):
        abort(
            code=status.HTTP_400_BAD_REQUEST,
            detail=f"The number of videos exceeds the maximum currently allowed "
            f"({len(people_counter_input.videos_storage_paths)} > "
            f"{config.api.maximum_videos_number})",
        )

    try:
        _validate_video_storage_paths(
            videos_storage_paths=people_counter_input.videos_storage_paths,
            expected_bucket_name=VIDEOS_TO_COUNT_BUCKET,
        )
    except ValueError as value_error:
        abort(code=status.HTTP_400_BAD_REQUEST, detail=str(value_error))

    video_assets = make_assets(
        assets_paths=people_counter_input.videos_storage_paths,
        storage_client=storage_client,
        asset_type=AssetType.VIDEO,
    )
    assets_ids = [video_asset.get_hash() for video_asset in video_assets]

    _upload_people_job_document(
        firestore_client=firestore_client,
        firestore_jobs_collection=firestore_jobs_collection,
        job_id=job_id,
        assets_ids=assets_ids,
    )

    counted_videos_storage_paths = None
    if people_counter_input.save_counted_videos is True:
        counted_videos_storage_paths = [
            _create_counted_video_storage_path(
                asset_id=asset_id,
                asset_path=video_asset.asset_path,
                counted_videos_bucket=COUNTED_VIDEOS_BUCKET,
                job_id=job_id,
            )
            for asset_id, video_asset in zip(assets_ids, video_assets)
        ]

    job_name = f"count-people-{job_id}"
    job_command_args = [
        "-m",
        "people_counting.jobs.count_people",
    ]
    job_environment_variables = {
        "PROJECT_ID": PROJECT_ID,
        "REGION": REGION,
        "OBJECT_DETECTION_MODEL_NAME": OBJECT_DETECTION_MODEL_NAME,
        "MODEL_INSTANTIATOR_HOST": MODEL_INSTANTIATOR_HOST,
        "FIRESTORE_RESULTS_COLLECTION": FIRESTORE_RESULTS_COLLECTION,
        "JOB_ID": job_id,
        "VIDEOS_STORAGE_PATHS": " ".join(people_counter_input.videos_storage_paths),
    }
    if counted_videos_storage_paths is not None:
        job_environment_variables["COUNTED_VIDEOS_STORAGE_PATHS"] = " ".join(
            counted_videos_storage_paths
        )

    cloud_run_job_manager.create_job(
        job_name=job_name,
        job_config=JobConfig(
            container_uri=config.job.container_uri,
            cpu=config.job.cpu,
            memory=config.job.memory,
            command=["python"],
            command_args=job_command_args,
            environment_variables=job_environment_variables,
        ),
        override_if_existing=True,
    )
    cloud_run_job_manager.run_job(job_name=job_name)

    return _launched_job_response(
        response=response,
        job_id=job_id,
    )


# used for debugging purposes only
@router.post(
    routes.PeopleCounter.count_people_real_time,
    status_code=status.HTTP_200_OK,
)
def count_people_real_time(
    people_counter_input: PeopleCounterRealTimeInput,
    response: Response,
    people_counter: PeopleCounter = Depends(use_people_counter),
    storage_client: StorageClient = Depends(use_storage_client),
) -> PeopleCounterRealTimeOutput:
    video_storage_path = people_counter_input.video_storage_path

    _validate_video_storage_path(
        video_storage_path=video_storage_path,
        expected_bucket_name=VIDEOS_TO_COUNT_BUCKET,
    )

    video_asset = make_asset(
        asset_path=people_counter_input.video_storage_path,
        storage_client=storage_client,
    )

    counted_video_storage_path = None
    if people_counter_input.save_counted_video is not None:
        counted_video_storage_path = _create_counted_video_storage_path(
            asset_id=video_asset.get_hash(),
            asset_path=video_asset.asset_path,
            counted_videos_bucket=COUNTED_VIDEOS_BUCKET,
        )

    statistics = count_people_with_upload(
        people_counter=people_counter,
        storage_client=storage_client,
        video_asset=video_asset,
        counted_video_storage_path=counted_video_storage_path,
    )

    return _real_time_response(
        response=response,
        statistics=statistics,
        counted_video_storage_path=counted_video_storage_path,
    )
