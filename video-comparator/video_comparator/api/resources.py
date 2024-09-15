from core.routes.video_comparator import routes
from core.schemas.video_comparator import ResourcesOutput
from fastapi import APIRouter, Depends
from starlette import status

from video_comparator.api.dependencies import use_config
from video_comparator.config import Config
from video_comparator.environment_variables import (
    FIRESTORE_JOBS_COLLECTION,
    JOB_RESULTS_BUCKET,
    VIDEOS_TO_COMPARE_BUCKET,
)

router = APIRouter(prefix=f"/{routes.Resources.prefix}", tags=[routes.Resources.prefix])


@router.get(
    routes.Resources.videos_to_compare_bucket,
    status_code=status.HTTP_200_OK,
)
def get_videos_to_compare_bucket() -> ResourcesOutput:
    return ResourcesOutput(resource=VIDEOS_TO_COMPARE_BUCKET)


@router.get(
    routes.Resources.job_results_bucket,
    status_code=status.HTTP_200_OK,
)
def get_job_results_bucket() -> ResourcesOutput:
    return ResourcesOutput(resource=JOB_RESULTS_BUCKET)


@router.get(
    routes.Resources.firestore_jobs_collection,
    status_code=status.HTTP_200_OK,
)
def get_firestore_jobs_collection() -> ResourcesOutput:
    return ResourcesOutput(resource=FIRESTORE_JOBS_COLLECTION)


@router.get(
    routes.Resources.maximum_videos_number,
    status_code=status.HTTP_200_OK,
)
def get_maximum_videos_number(
    config: Config = Depends(use_config),
) -> ResourcesOutput:
    return ResourcesOutput(resource=str(config.api.maximum_videos_number))
