import os

from fastapi import Depends
from google.cloud import firestore  # pylint: disable=no-name-in-module
from google.cloud import storage
from people_counting.dependencies import get_people_counter_with_package_config


def get_storage_client():
    return storage.Client(project=os.environ["PROJECT_ID"])


def get_bucket_of_videos_to_count(
    storage_client: storage.Client = Depends(get_storage_client),
):
    return storage_client.bucket(os.environ["VIDEOS_TO_COUNT_BUCKET"])


def get_bucket_of_counted_videos(
    storage_client: storage.Client = Depends(get_storage_client),
):
    return storage_client.bucket(os.environ["COUNTED_VIDEOS_BUCKET"])


def get_people_counter():
    return get_people_counter_with_package_config()


def get_firestore_results_collection():
    return firestore.Client().collection(os.environ["FIRESTORE_RESULTS_COLLECTION"])
