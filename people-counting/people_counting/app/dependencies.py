from functools import lru_cache

from core.client.object_detection import ObjectDetectionClient
from core.google.cloud_run_job_manager import CloudRunJobManager
from core.google.firestore_client import FirestoreClient
from core.google.storage_client import StorageClient
from fastapi import Depends
from omegaconf import DictConfig

from people_counting.config import cfg
from people_counting.environment_variables import (
    COUNTED_VIDEOS_BUCKET,
    FIRESTORE_JOBS_COLLECTION,
    GOOGLE_APPLICATION_CREDENTIALS,
    OBJECT_DETECTION_HOST,
    PROJECT_ID,
    REGION,
    RESULTS_BUCKET,
    SAMPLES_BUCKET,
)
from people_counting.people_counter import PeopleCounter


@lru_cache
def use_config() -> DictConfig:
    return cfg


@lru_cache
def use_object_detection_host() -> str:
    return OBJECT_DETECTION_HOST


@lru_cache
def use_firestore_jobs_collection() -> str:
    return FIRESTORE_JOBS_COLLECTION


@lru_cache
def use_google_application_credentials() -> str:
    return GOOGLE_APPLICATION_CREDENTIALS


@lru_cache
def use_project_id() -> str:
    return PROJECT_ID


@lru_cache
def use_region() -> str:
    return REGION


@lru_cache()
def use_counted_videos_bucket() -> str:
    return COUNTED_VIDEOS_BUCKET


@lru_cache()
def use_results_bucket() -> str:
    return RESULTS_BUCKET


@lru_cache()
def use_samples_bucket() -> str:
    return SAMPLES_BUCKET


@lru_cache
def use_storage_client(
    google_application_credentials: str = Depends(use_google_application_credentials),
    project_id: str = Depends(use_project_id),
) -> StorageClient:
    return StorageClient(key_path=google_application_credentials, project_id=project_id)


@lru_cache
def use_firestore_client() -> FirestoreClient:
    return FirestoreClient(
        key_path=GOOGLE_APPLICATION_CREDENTIALS, project_id=PROJECT_ID
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
def use_object_detection_client(
    object_detection_host: str = Depends(use_object_detection_host),
    project_id: str = Depends(use_project_id),
) -> ObjectDetectionClient:
    return ObjectDetectionClient(host=object_detection_host, project_id=project_id)


@lru_cache
def use_people_counter(
    config: DictConfig = Depends(use_config),
    object_detection_client: ObjectDetectionClient = Depends(
        use_object_detection_client
    ),
) -> PeopleCounter:
    return PeopleCounter(
        object_detection_client=object_detection_client,
        confidence_threshold=config.postprocessing.confidence_threshold,
        algorithm_config=config.algorithm,
        image_width=config.preprocessing.image_width,
        video_outputs_directory=config.paths.outputs_directory,
    )
