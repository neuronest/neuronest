from typing import Optional

from core.client.model_client.video_comparator import VideoComparatorModelClient
from core.client.model_instantiator import ModelInstantiatorClient
from core.google.storage_client import StorageClient
from core.google.vertex_ai_manager import VertexAIManager

from video_comparator.services.embedding_manager import EmbeddingManager


def create_video_comparator_model_client(
    region: str,
    project_id: str,
    model_instantiator_host: str,
    model_name: str,
) -> VideoComparatorModelClient:
    return VideoComparatorModelClient(
        vertex_ai_manager=VertexAIManager(
            location=region,
            project_id=project_id,
        ),
        model_instantiator_client=ModelInstantiatorClient(
            host=model_instantiator_host,
        ),
        model_name=model_name,
    )


def create_storage_client(project_id: Optional[str] = None) -> StorageClient:
    return StorageClient(project_id=project_id)


def create_embedding_manager(
    storage_client: StorageClient, bucket_name: str
) -> EmbeddingManager:
    return EmbeddingManager(storage_client=storage_client, bucket_name=bucket_name)
