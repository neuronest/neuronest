from core.routes.people_counting import routes
from core.schemas.people_counting import ResourcesOutput
from fastapi import APIRouter, Depends
from omegaconf import DictConfig
from starlette import status

from people_counting.api.dependencies import use_config
from people_counting.environment_variables import (
    FIRESTORE_JOBS_COLLECTION,
    FIRESTORE_RESULTS_COLLECTION,
    VIDEOS_TO_COUNT_BUCKET,
)

router = APIRouter(prefix=f"/{routes.Resources.prefix}", tags=[routes.Resources.prefix])


@router.get(
    routes.Resources.videos_to_count_bucket,
    status_code=status.HTTP_200_OK,
)
def get_videos_to_count_bucket() -> ResourcesOutput:
    return ResourcesOutput(resource=VIDEOS_TO_COUNT_BUCKET)


@router.get(
    routes.Resources.firestore_results_collection,
    status_code=status.HTTP_200_OK,
)
def get_firestore_results_collection() -> ResourcesOutput:
    return ResourcesOutput(resource=FIRESTORE_RESULTS_COLLECTION)


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
    config: DictConfig = Depends(use_config),
) -> ResourcesOutput:
    return ResourcesOutput(resource=str(config.api.maximum_videos_number))
