import os

import pytest
from core.client.model_instantiator import ModelInstantiatorClient
from core.client.video_comparator import VideoComparatorClient
from core.google.storage_client import StorageClient

from tests.environment_variables import (
    GOOGLE_APPLICATION_CREDENTIALS,
    MODEL_INSTANTIATOR_HOST,
    MODEL_NAME,
    PROJECT_ID,
    REGION,
    VIDEO_COMPARATOR_URL,
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


@pytest.fixture(name="video_comparator_url", scope="session")
def fixture_video_comparator_url() -> str:
    return VIDEO_COMPARATOR_URL


@pytest.fixture(name="storage_client", scope="session")
def fixture_storage_client(google_application_credentials: str) -> StorageClient:
    return StorageClient(key_path=google_application_credentials)


@pytest.fixture(name="model_instantiator_client", scope="session")
def fixture_model_instantiator_client(
    model_instantiator_host: str, google_application_credentials: str
) -> ModelInstantiatorClient:
    return ModelInstantiatorClient(
        host=model_instantiator_host, key_path=google_application_credentials
    )


@pytest.fixture(name="video_comparator_client", scope="session")
def fixture_video_comparator_client(
    video_comparator_url: str, google_application_credentials: str, project_id: str
) -> VideoComparatorClient:
    return VideoComparatorClient(
        host=video_comparator_url,
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
        # if using pytest-xdist parallel workers, we want the teardown to be executed
        # only with the main worker to prevent undesired cases
        # see https://pytest-xdist.readthedocs.io/en/latest/how-to.html#making-session-scoped-fixtures-execute-only-once
        if os.getenv("PYTEST_XDIST_WORKER") == "gw0":
            model_instantiator_client.uninstantiate(model_name)
