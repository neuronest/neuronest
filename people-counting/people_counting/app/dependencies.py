from functools import lru_cache

from core.client.model_client.object_detection import ObjectDetectionModelClient
from core.client.model_instantiator import ModelInstantiatorClient
from core.google.cloud_run_job_manager import CloudRunJobManager
from core.google.firestore_client import FirestoreClient
from core.google.storage_client import StorageClient
from core.google.vertex_ai_manager import VertexAIManager
from fastapi import Depends
from omegaconf import DictConfig

from people_counting.config import cfg
from people_counting.environment_variables import (
    FIRESTORE_JOBS_COLLECTION,
    GOOGLE_APPLICATION_CREDENTIALS,
    MODEL_INSTANTIATOR_HOST,
    OBJECT_DETECTION_MODEL_NAME,
    PROJECT_ID,
    REGION,
    VPC_NETWORK,
)
from people_counting.people_counter import PeopleCounter


@lru_cache
def use_config() -> DictConfig:
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
            location=REGION,
            project_id=PROJECT_ID,
            vpc_network=VPC_NETWORK,
        ),
        model_instantiator_client=ModelInstantiatorClient(
            key_path=GOOGLE_APPLICATION_CREDENTIALS,
            host=MODEL_INSTANTIATOR_HOST,
        ),
        model_name=OBJECT_DETECTION_MODEL_NAME,
    )


@lru_cache
def use_people_counter(
    config: DictConfig = Depends(use_config),
    object_detection_model_client: ObjectDetectionModelClient = Depends(
        use_object_detection_model_client
    ),
) -> PeopleCounter:
    return PeopleCounter(
        object_detection_model_client=object_detection_model_client,
        confidence_threshold=config.postprocessing.confidence_threshold,
        algorithm_config=config.algorithm,
        image_width=config.preprocessing.image_width,
        video_outputs_directory=config.paths.outputs_directory,
    )
