import os

from fastapi import Depends
from google.cloud import firestore  # pylint: disable=no-name-in-module
from google.cloud import storage
from people_counting.config import cfg as config_counting
from people_counting.people_counter import PeopleCounter


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
    return PeopleCounter(
        model_config=config_counting.model,
        algorithm_config=config_counting.algorithm,
        image_width=config_counting.preprocessing.image_width,
        video_outputs_directory=config_counting.paths.outputs_directory,
    )


def get_firestore_results_collection():
    return firestore.Client().collection(os.environ["FIRESTORE_RESULTS_COLLECTION"])
