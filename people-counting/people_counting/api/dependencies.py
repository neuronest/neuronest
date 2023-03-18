from fastapi import Depends
from google.cloud import firestore, storage

from people_counting.dependencies import get_people_counter_with_package_config
from people_counting.environment_variables import (
    COUNTED_VIDEOS_BUCKET,
    FIRESTORE_RESULTS_COLLECTION,
    PROJECT_ID,
    VIDEOS_TO_COUNT_BUCKET,
)


def get_storage_client():
    return storage.Client(project=PROJECT_ID)


def get_bucket_of_videos_to_count(
    storage_client: storage.Client = Depends(get_storage_client),
):
    return storage_client.bucket(VIDEOS_TO_COUNT_BUCKET)


def get_bucket_of_counted_videos(
    storage_client: storage.Client = Depends(get_storage_client),
):
    return storage_client.bucket(COUNTED_VIDEOS_BUCKET)


def get_people_counter():
    return get_people_counter_with_package_config()


def get_firestore_results_collection():
    return firestore.Client().collection(FIRESTORE_RESULTS_COLLECTION)
