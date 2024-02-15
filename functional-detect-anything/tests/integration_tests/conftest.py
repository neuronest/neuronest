import os
from typing import Optional

import cv2 as cv
import numpy as np
import pytest
from core.client.model_instantiator import ModelInstantiatorClient
from core.client.object_detection import ObjectDetectionClient
from core.google.vertex_ai_manager import VertexAIManager

from ..environment_variables import (
    GOOGLE_APPLICATION_CREDENTIALS,
    MODEL_INSTANTIATOR_HOST,
    MODEL_NAME,
    PROJECT_ID,
    REGION,
)


@pytest.fixture(name="google_application_credentials", scope="session")
def fixture_google_application_credentials() -> Optional[str]:
    return GOOGLE_APPLICATION_CREDENTIALS


@pytest.fixture(name="model_instantiator_host", scope="session")
def fixture_model_instantiator_host() -> str:
    return MODEL_INSTANTIATOR_HOST


@pytest.fixture(name="model_name", scope="session")
def fixture_model_name() -> str:
    return MODEL_NAME


@pytest.fixture(name="project_id", scope="session")
def fixture_project_id() -> str:
    return PROJECT_ID


@pytest.fixture(name="region", scope="session")
def fixture_region() -> str:
    return REGION


@pytest.fixture(name="image_directory", scope="session")
def fixture_image_directory() -> str:
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"
    )


@pytest.fixture(name="image", scope="session")
def fixture_sample(image_directory: str) -> np.ndarray:
    return cv.imread(os.path.join(image_directory, "sample.png"))


@pytest.fixture(name="vertex_ai_manager", scope="session")
def fixture_vertex_ai_manager(
    region: str, project_id: str, google_application_credentials: Optional[str]
) -> VertexAIManager:
    return VertexAIManager(
        location=region,
        key_path=google_application_credentials,
        project_id=project_id,
    )


@pytest.fixture(name="model_instantiator_client", scope="session")
def fixture_model_instantiator_client(
    model_instantiator_host: str, google_application_credentials: Optional[str]
) -> ModelInstantiatorClient:
    return ModelInstantiatorClient(
        host=model_instantiator_host,
        key_path=google_application_credentials,
    )


@pytest.fixture(name="object_detection_client", scope="session")
def fixture_object_detection_client(
    vertex_ai_manager: VertexAIManager,
    model_instantiator_client: ModelInstantiatorClient,
    model_name: str,
):
    return ObjectDetectionClient(
        vertex_ai_manager=vertex_ai_manager,
        model_instantiator_client=model_instantiator_client,
        model_name=model_name,
    )


@pytest.fixture(name="uninstantiate_teardown", scope="session")
def fixture_uninstantiate_teardown(
    model_instantiator_client: ModelInstantiatorClient,
    model_name: str,
):
    try:
        yield

    finally:
        model_instantiator_client.uninstantiate(model_name)
