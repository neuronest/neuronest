import os
import tempfile
import uuid

import pytest
from core.client.model_instantiator import ModelInstantiatorClient
from core.client.video_comparator import VideoComparatorClient
from core.google.storage_client import StorageClient
from core.google.vertex_ai_manager import VertexAIManager
from core.path import GSPath

from ..environment_variables import (
    GOOGLE_APPLICATION_CREDENTIALS,
    MODEL_INSTANTIATOR_HOST,
    MODEL_NAME,
    PROJECT_ID,
    REGION,
)


@pytest.fixture(name="model_instantiator_client", scope="session")
def fixture_model_instantiator_client() -> ModelInstantiatorClient:
    return ModelInstantiatorClient(
        host=MODEL_INSTANTIATOR_HOST,
        key_path=GOOGLE_APPLICATION_CREDENTIALS,
    )


@pytest.fixture(name="video_comparator_client", scope="session")
def fixture_video_comparator_client(model_instantiator_client: ModelInstantiatorClient):

    return VideoComparatorClient(
        vertex_ai_manager=VertexAIManager(
            key_path=GOOGLE_APPLICATION_CREDENTIALS,
            location=REGION,
            project_id=PROJECT_ID,
        ),
        model_instantiator_client=model_instantiator_client,
        model_name=MODEL_NAME,
        project_id=PROJECT_ID,
    )


@pytest.fixture(name="model_name", scope="session")
def fixture_model_name() -> str:
    return MODEL_NAME


@pytest.fixture(name="uninstantiate_teardown", scope="session")
def fixture_uninstantiate_teardown(
    model_instantiator_client: ModelInstantiatorClient,
    model_name: str,
):
    try:
        yield

    finally:
        model_instantiator_client.uninstantiate(model_name)


# Fixture to download a video given its GCS URL
@pytest.fixture(name="best_to_worst_matching_videos_pairs", scope="session")
def fixture_best_to_worst_matching_videos_pairs(request):
    best_to_worst_matching_videos_pairs = request.param
    best_to_worst_matching_videos_pairs_local_dir = os.path.join(
        tempfile.gettempdir(), str(uuid.uuid4())
    )
    os.makedirs(best_to_worst_matching_videos_pairs_local_dir)
    best_to_worst_matching_videos_pairs_local_paths = []

    storage_client = StorageClient()
    for video_path, other_video_path in best_to_worst_matching_videos_pairs:
        video_path = GSPath(video_path)
        other_video_path = GSPath(other_video_path)

        video_local_path = os.path.join(
            best_to_worst_matching_videos_pairs_local_dir,
            f"{video_path.bucket}_"
            f"{video_path.blob_name.replace(video_path.SEPARATOR, '_')}",
        )
        other_video_local_path = os.path.join(
            best_to_worst_matching_videos_pairs_local_dir,
            f"{other_video_path.bucket}_"
            f"{other_video_path.blob_name.replace(other_video_path.SEPARATOR, '_')}",
        )

        storage_client.download_blob_to_file(
            bucket_name=video_path.bucket,
            source_blob_name=video_path.blob_name,
            destination_file_name=video_local_path,
        )
        storage_client.download_blob_to_file(
            bucket_name=other_video_path.bucket,
            source_blob_name=other_video_path.blob_name,
            destination_file_name=other_video_local_path,
        )

        best_to_worst_matching_videos_pairs_local_paths.append(
            (video_local_path, other_video_local_path)
        )

    yield best_to_worst_matching_videos_pairs_local_paths

    for (
        video_local_path,
        other_video_local_path,
    ) in best_to_worst_matching_videos_pairs_local_paths:
        os.remove(video_local_path)
        os.remove(other_video_local_path)
