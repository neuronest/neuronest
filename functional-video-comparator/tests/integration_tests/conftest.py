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


@pytest.fixture
def video_comparator_client():

    return VideoComparatorClient(
        vertex_ai_manager=VertexAIManager(
            key_path=GOOGLE_APPLICATION_CREDENTIALS,
            location=REGION,
            project_id=PROJECT_ID,
        ),
        model_instantiator_client=ModelInstantiatorClient(
            key_path=GOOGLE_APPLICATION_CREDENTIALS, host=MODEL_INSTANTIATOR_HOST
        ),
        model_name=MODEL_NAME,
        project_id=PROJECT_ID,
    )
