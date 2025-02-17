from core.routes.service_evaluator import routes
from core.schemas.service_evaluator import ResourcesOutput
from fastapi import APIRouter, Depends
from omegaconf import DictConfig
from starlette import status

from service_evaluator.api.dependencies import (
    use_config,
    use_firestore_jobs_collection,
    use_region,
)

router = APIRouter(prefix=f"/{routes.Resources.prefix}", tags=[routes.Resources.prefix])


@router.get(
    routes.Resources.region,
    status_code=status.HTTP_200_OK,
)
def get_region(
    region: str = Depends(use_region),
) -> ResourcesOutput:
    return ResourcesOutput(resource=region)


@router.get(
    routes.Resources.firestore_jobs_collection,
    status_code=status.HTTP_200_OK,
)
def get_firestore_jobs_collection(
    firestore_jobs_collection: str = Depends(use_firestore_jobs_collection),
) -> ResourcesOutput:
    return ResourcesOutput(resource=firestore_jobs_collection)


@router.get(
    routes.Resources.bigquery_dataset_name,
    status_code=status.HTTP_200_OK,
)
def get_bigquery_dataset_name(
    config: DictConfig = Depends(use_config),
) -> ResourcesOutput:
    return ResourcesOutput(resource=config.bigquery.dataset.name)
