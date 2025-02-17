from typing import Optional

from core.client.object_detection import ObjectDetectionClient
from core.google.storage_client import StorageClient
from omegaconf import DictConfig

from people_counting.people_counter import PeopleCounter


def create_object_detection_client(
    project_id: str,
    object_detection_host: str,
) -> ObjectDetectionClient:
    return ObjectDetectionClient(host=object_detection_host, project_id=project_id)


def create_people_counter(
    project_id: str,
    object_detection_host: str,
    config: DictConfig,
) -> PeopleCounter:
    object_detection_client = create_object_detection_client(
        project_id=project_id,
        object_detection_host=object_detection_host,
    )

    return PeopleCounter(
        object_detection_client=object_detection_client,
        confidence_threshold=config.postprocessing.confidence_threshold,
        algorithm_config=config.algorithm,
        image_width=config.preprocessing.image_width,
        video_outputs_directory=config.paths.outputs_directory,
    )


def create_storage_client(project_id: Optional[str] = None) -> StorageClient:
    return StorageClient(project_id=project_id)
