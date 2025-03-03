import os
from typing import Optional

import pytest
from core.client.model_instantiator import ModelInstantiatorClient
from core.client.object_detection import ObjectDetectionClient
from core.google.storage_client import StorageClient

from tests.environment_variables import (
    GOOGLE_APPLICATION_CREDENTIALS,
    MODEL_INSTANTIATOR_HOST,
    MODEL_NAME,
    OBJECT_DETECTION_URL,
    PROJECT_ID,
)


@pytest.fixture(name="google_application_credentials", scope="session")
def fixture_google_application_credentials() -> str:
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


@pytest.fixture(name="object_detection_url", scope="session")
def fixture_object_detection_url() -> str:
    return OBJECT_DETECTION_URL


@pytest.fixture(name="storage_client", scope="session")
def fixture_storage_client() -> StorageClient:
    return StorageClient()


@pytest.fixture(name="model_instantiator_client", scope="session")
def fixture_model_instantiator_client(
    model_instantiator_host: str,
    google_application_credentials: Optional[str],
) -> ModelInstantiatorClient:
    return ModelInstantiatorClient(
        host=model_instantiator_host, key_path=google_application_credentials
    )


@pytest.fixture(name="image_directory", scope="session")
def fixture_image_directory() -> str:
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"
    )


@pytest.fixture(name="sample_path", scope="session")
def fixture_sample_path(image_directory: str) -> str:
    return os.path.join(image_directory, "sample.png")


@pytest.fixture(name="object_detection_client", scope="session")
def fixture_object_detection_client(
    object_detection_url: str,
    project_id: str,
    google_application_credentials: Optional[str],
) -> ObjectDetectionClient:
    return ObjectDetectionClient(
        host=object_detection_url,
        key_path=google_application_credentials,
        project_id=project_id,
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
