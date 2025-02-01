from functools import lru_cache

from core.client.model_client.object_detection import ObjectDetectionModelClient
from core.client.model_instantiator import ModelInstantiatorClient
from core.google.cloud_run_job_manager import CloudRunJobManager
from core.google.firestore_client import FirestoreClient
from core.google.storage_client import StorageClient
from core.google.vertex_ai_manager import VertexAIManager

from object_detection.config import Config, cfg
from object_detection.environment_variables import (
    FIRESTORE_JOBS_COLLECTION,
    GOOGLE_APPLICATION_CREDENTIALS,
    MODEL_INSTANTIATOR_HOST,
    MODEL_NAME,
    PROJECT_ID,
    REGION,
    SAMPLES_BUCKET,
    VERTEX_LOCATION,
)


@lru_cache
def use_config() -> Config:
    return cfg


@lru_cache
def use_storage_client() -> StorageClient:
    return StorageClient(key_path=GOOGLE_APPLICATION_CREDENTIALS, project_id=PROJECT_ID)


@lru_cache
def use_firestore_client() -> FirestoreClient:
    return FirestoreClient(
        key_path=GOOGLE_APPLICATION_CREDENTIALS, project_id=PROJECT_ID
    )


@lru_cache
def use_firestore_jobs_collection() -> str:
    return FIRESTORE_JOBS_COLLECTION


@lru_cache
def use_samples_bucket() -> str:
    return SAMPLES_BUCKET


@lru_cache
def use_cloud_run_job_manager() -> CloudRunJobManager:
    return CloudRunJobManager(
        key_path=GOOGLE_APPLICATION_CREDENTIALS,
        project_id=PROJECT_ID,
        location=REGION,
    )


@lru_cache
def use_object_detection_model_client() -> ObjectDetectionModelClient:
    return ObjectDetectionModelClient(
        vertex_ai_manager=VertexAIManager(
            key_path=GOOGLE_APPLICATION_CREDENTIALS,
            location=VERTEX_LOCATION,
            project_id=PROJECT_ID,
        ),
        model_instantiator_client=ModelInstantiatorClient(
            key_path=GOOGLE_APPLICATION_CREDENTIALS,
            host=MODEL_INSTANTIATOR_HOST,
        ),
        model_name=MODEL_NAME,
    )
