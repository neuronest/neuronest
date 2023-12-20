from typing import Optional

from core.client.model_instantiator import ModelInstantiatorClient
from core.client.object_detection import ObjectDetectionClient
from core.google.firestore_client import FirestoreClient
from core.google.storage_client import StorageClient
from core.google.vertex_ai_manager import VertexAIManager
from omegaconf import DictConfig

from people_counting.people_counter import PeopleCounter


def create_object_detection_client(
    project_id: str,
    region: str,
    model_instantiator_host: str,
    object_detection_model_name: str,
) -> ObjectDetectionClient:
    return ObjectDetectionClient(
        vertex_ai_manager=VertexAIManager(
            location=region,
            project_id=project_id,
        ),
        model_instantiator_client=ModelInstantiatorClient(
            host=model_instantiator_host,
        ),
        model_name=object_detection_model_name,
    )


def create_people_counter(
    project_id: str,
    region: str,
    model_instantiator_host: str,
    object_detection_model_name: str,
    config: DictConfig,
) -> PeopleCounter:
    object_detection_client = create_object_detection_client(
        project_id=project_id,
        region=region,
        model_instantiator_host=model_instantiator_host,
        object_detection_model_name=object_detection_model_name,
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


def create_firestore_client(project_id: Optional[str] = None) -> FirestoreClient:
    return FirestoreClient(project_id=project_id)
