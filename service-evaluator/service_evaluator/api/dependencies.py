import json
from functools import lru_cache
from typing import Dict

from core.google.cloud_run_job_manager import CloudRunJobManager
from core.google.cloud_run_manager import CloudRunManager
from core.google.firestore_client import FirestoreClient
from core.google.vertex_ai_manager import VertexAIManager
from core.schemas.image_name import ImageName
from core.schemas.service_evaluator import EvaluatedServiceName
from omegaconf import DictConfig

from service_evaluator.config import cfg
from service_evaluator.environment_variables import (
    FIRESTORE_JOBS_COLLECTION,
    GOOGLE_APPLICATION_CREDENTIALS,
    JOB_PREFIX_NAME,
    PROJECT_ID,
    REGION,
    SERIALIZED_SERVICE_CLIENT_PARAMETERS,
    SERVICE_IMAGE_NAME,
    SERVICE_NAME,
    SERVICE_URL,
)


@lru_cache
def use_config() -> DictConfig:
    return cfg


@lru_cache
def use_firestore_jobs_collection() -> str:
    return FIRESTORE_JOBS_COLLECTION


@lru_cache
def use_service_name() -> EvaluatedServiceName:
    return EvaluatedServiceName(SERVICE_NAME)


@lru_cache
def use_service_url() -> str:
    return SERVICE_URL


@lru_cache
def use_service_image_name() -> ImageName:
    return SERVICE_IMAGE_NAME


@lru_cache
def use_job_prefix_name() -> str:
    return JOB_PREFIX_NAME


@lru_cache
def use_service_client_parameters() -> Dict[str, str]:
    return json.loads(SERIALIZED_SERVICE_CLIENT_PARAMETERS)


@lru_cache
def use_firestore_client() -> FirestoreClient:
    return FirestoreClient(
        key_path=GOOGLE_APPLICATION_CREDENTIALS,
    )


@lru_cache
def use_cloud_run_manager() -> CloudRunManager:
    return CloudRunManager(
        key_path=GOOGLE_APPLICATION_CREDENTIALS,
        project_id=PROJECT_ID,
        location=REGION,
    )


@lru_cache
def use_cloud_run_job_manager() -> CloudRunJobManager:
    return CloudRunJobManager(
        key_path=GOOGLE_APPLICATION_CREDENTIALS,
        project_id=PROJECT_ID,
        location=REGION,
    )


@lru_cache
def use_vertex_ai_manager() -> VertexAIManager:
    return VertexAIManager(
        location=REGION,
        key_path=GOOGLE_APPLICATION_CREDENTIALS,
        project_id=PROJECT_ID,
    )
