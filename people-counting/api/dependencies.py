from api.config import config as config_api
from fastapi import Depends
from google.cloud import firestore, storage  # pylint: disable=no-name-in-module
from people_counting.config import cfg as config_counting
from people_counting.people_counter import PeopleCounter


def get_storage_client():
    return storage.Client(project=config_api.general.project)


def get_bucket_of_videos_to_count(
    storage_client: storage.Client = Depends(get_storage_client),
):
    return storage_client.bucket(config_api.storage.videos_to_count_bucket)


def get_bucket_of_counted_videos(
    storage_client: storage.Client = Depends(get_storage_client),
):
    return storage_client.bucket(config_api.storage.counted_videos_bucket)


def get_people_counter():
    return PeopleCounter(
        model_config=config_counting.model,
        algorithm_config=config_counting.algorithm,
        image_width=config_counting.preprocessing.image_width,
        video_outputs_directory=config_counting.paths.outputs_directory,
    )


def get_firestore_results_collection():
    return firestore.Client().collection(config_api.firestore.results_collection)
