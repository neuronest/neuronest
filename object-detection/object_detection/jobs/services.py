from typing import Optional

from core.client.model_client.object_detection import ObjectDetectionModelClient
from core.client.model_instantiator import ModelInstantiatorClient
from core.google.storage_client import StorageClient
from core.google.vertex_ai_manager import VertexAIManager


def create_object_detection_model_client(
    project_id: str,
    vertex_location: str,
    model_instantiator_host: str,
    model_name: str,
) -> ObjectDetectionModelClient:
    return ObjectDetectionModelClient(
        vertex_ai_manager=VertexAIManager(
            location=vertex_location,
            project_id=project_id,
        ),
        model_instantiator_client=ModelInstantiatorClient(
            host=model_instantiator_host,
        ),
        model_name=model_name,
    )


def create_storage_client(project_id: Optional[str] = None) -> StorageClient:
    return StorageClient(project_id=project_id)
