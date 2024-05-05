import pytest
from core.client.model_instantiator import ModelInstantiatorClient
from core.client.video_comparator import VideoComparatorClient
from core.google.vertex_ai_manager import VertexAIManager
from tests.environment_variables import (
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
