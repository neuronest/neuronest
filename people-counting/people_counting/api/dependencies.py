from core.google.storage_client import StorageClient
from fastapi import Depends
from google.cloud import firestore

from people_counting.dependencies import get_people_counter_with_package_config
from people_counting.environment_variables import (
    COUNTED_VIDEOS_BUCKET,
    FIRESTORE_RESULTS_COLLECTION,
    PROJECT_ID,
)


def get_storage_client():
    return StorageClient(project_id=PROJECT_ID)


def get_bucket_of_counted_videos(
    storage_client: StorageClient = Depends(get_storage_client),
):
    return storage_client.client.bucket(COUNTED_VIDEOS_BUCKET)


def get_people_counter():
    return get_people_counter_with_package_config()


def get_firestore_results_collection():
    return firestore.Client(project=PROJECT_ID).collection(FIRESTORE_RESULTS_COLLECTION)
