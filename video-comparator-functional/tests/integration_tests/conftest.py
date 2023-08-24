from typing import Optional

import pytest
import requests
from core.client.model_instantiator import ModelInstantiatorClient
from core.client.video_comparator import VideoComparatorClient
from core.google.vertex_ai_manager import VertexAIManager
from tests.environment_variables import (
    GOOGLE_APPLICATION_CREDENTIALS,
    MODEL_NAME,
    PROJECT_ID,
    REGION,
)

# @pytest.fixture
# def people_counting_url():
#     return os.environ["PEOPLE_COUNTING_URL"]
#
#
# @pytest.fixture
# def project_id():
#     return os.environ["PROJECT_ID"]


class FakeModelInstantiatorClient(ModelInstantiatorClient):
    def instantiate(self, model_name: str) -> Optional[requests.Response]:
        response = requests.Response()
        response.status_code = "201"

        return response

    def uninstantiate(self, model_name: str) -> requests.Response:
        response = requests.Response()
        response.status_code = "202"

        return response


@pytest.fixture
def video_comparator_client():

    fake_model_instantiator_client = FakeModelInstantiatorClient(
        key_path=GOOGLE_APPLICATION_CREDENTIALS, host="fake_model_instantiator_host"
    )
    vertex_ai_manager = VertexAIManager(
        key_path=GOOGLE_APPLICATION_CREDENTIALS, location=REGION, project_id=PROJECT_ID
    )
    object_detection_client = VideoComparatorClient(
        vertex_ai_manager=vertex_ai_manager,
        model_instantiator_client=fake_model_instantiator_client,
        model_name=MODEL_NAME,
    )

    return object_detection_client


@pytest.fixture
def best_to_worst_matching_videos_pairs():
    return [(), ()]
