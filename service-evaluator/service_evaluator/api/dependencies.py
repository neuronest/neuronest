from functools import lru_cache

from core.google.cloud_run_job_manager import CloudRunJobManager
from core.google.firestore_client import FirestoreClient
from core.google.vertex_ai_manager import VertexAIManager
from core.schemas.service_evaluator import EvaluatedServiceName
from fastapi import Depends
from omegaconf import DictConfig

from service_evaluator.config import cfg
from service_evaluator.environment_variables import (
    FIRESTORE_JOBS_COLLECTION,
    GOOGLE_APPLICATION_CREDENTIALS,
    JOB_PREFIX_NAME,
    PROJECT_ID,
    REGION,
    SERIALIZED_SERVICE_CLIENT_PARAMETERS,
    SERVICE_NAME,
)


@lru_cache
def use_config() -> DictConfig:
    return cfg


@lru_cache
def use_project_id() -> str:
    return PROJECT_ID


@lru_cache
def use_region() -> str:
    return REGION


@lru_cache
def use_google_application_credentials() -> str:
    return GOOGLE_APPLICATION_CREDENTIALS


@lru_cache
def use_firestore_jobs_collection() -> str:
    return FIRESTORE_JOBS_COLLECTION


@lru_cache
def use_service_name() -> EvaluatedServiceName:
    return EvaluatedServiceName(SERVICE_NAME)


@lru_cache
def use_job_prefix_name() -> str:
    return JOB_PREFIX_NAME


@lru_cache
def use_serialized_service_client_parameters() -> str:
    return SERIALIZED_SERVICE_CLIENT_PARAMETERS


@lru_cache
def use_firestore_client(
    google_application_credentials: str = Depends(use_google_application_credentials),
) -> FirestoreClient:
    return FirestoreClient(
        key_path=google_application_credentials,
    )


@lru_cache
def use_cloud_run_job_manager(
    google_application_credentials: str = Depends(use_google_application_credentials),
    project_id: str = Depends(use_project_id),
    region: str = Depends(use_region),
) -> CloudRunJobManager:
    return CloudRunJobManager(
        key_path=google_application_credentials,
        project_id=project_id,
        location=region,
    )


@lru_cache
def use_vertex_ai_manager(
    google_application_credentials: str = Depends(use_google_application_credentials),
    project_id: str = Depends(use_project_id),
    region: str = Depends(use_region),
) -> VertexAIManager:
    return VertexAIManager(
        location=region,
        key_path=google_application_credentials,
        project_id=project_id,
    )
