from core.routes.video_comparator import routes
from core.schemas.abstract.prediction_api_client import ResourcesOutput
from fastapi import APIRouter, Depends
from starlette import status

from video_comparator.app.dependencies import use_config
from video_comparator.config import Config
from video_comparator.environment_variables import (
    FIRESTORE_JOBS_COLLECTION,
    RESULTS_BUCKET,
    SAMPLES_BUCKET,
)

router = APIRouter(prefix=f"/{routes.Resources.prefix}", tags=[routes.Resources.prefix])


@router.get(
    routes.Resources.samples_bucket,
    status_code=status.HTTP_200_OK,
)
def get_samples_bucket() -> ResourcesOutput:
    return ResourcesOutput(resource=SAMPLES_BUCKET)


@router.get(
    routes.Resources.results_bucket,
    status_code=status.HTTP_200_OK,
)
def get_results_bucket() -> ResourcesOutput:
    return ResourcesOutput(resource=RESULTS_BUCKET)


@router.get(
    routes.Resources.firestore_jobs_collection,
    status_code=status.HTTP_200_OK,
)
def get_firestore_jobs_collection() -> ResourcesOutput:
    return ResourcesOutput(resource=FIRESTORE_JOBS_COLLECTION)


@router.get(
    routes.Resources.maximum_elements_number,
    status_code=status.HTTP_200_OK,
)
def get_maximum_elements_number(
    config: Config = Depends(use_config),
) -> ResourcesOutput:
    return ResourcesOutput(resource=str(config.app.maximum_elements_number))
