from typing import Optional

import pytest
from core.client.model_instantiator import ModelInstantiatorClient
from core.client.people_counting import PeopleCountingClient
from core.google.storage_client import StorageClient

from tests.environment_variables import (
    GOOGLE_APPLICATION_CREDENTIALS,
    MODEL_INSTANTIATOR_HOST,
    MODEL_NAME,
    PEOPLE_COUNTING_URL,
    PROJECT_ID,
)


@pytest.fixture(name="model_instantiator_host", scope="session")
def fixture_model_instantiator_host() -> str:
    return MODEL_INSTANTIATOR_HOST


@pytest.fixture(name="people_counting_url", scope="session")
def fixture_people_counting_url() -> str:
    return PEOPLE_COUNTING_URL


@pytest.fixture(name="project_id", scope="session")
def fixture_project_id() -> str:
    return PROJECT_ID


@pytest.fixture(name="model_name", scope="session")
def fixture_model_name() -> str:
    return MODEL_NAME


@pytest.fixture(name="google_application_credentials", scope="session")
def fixture_google_application_credentials() -> Optional[str]:
    return GOOGLE_APPLICATION_CREDENTIALS


@pytest.fixture(name="model_instantiator_client", scope="session")
def fixture_model_instantiator_client(
    model_instantiator_host: str,
) -> ModelInstantiatorClient:
    return ModelInstantiatorClient(
        host=model_instantiator_host,
    )


@pytest.fixture(name="people_counting_client", scope="session")
def fixture_people_counting_client(
    people_counting_url: str, project_id: str
) -> PeopleCountingClient:
    return PeopleCountingClient(host=people_counting_url, project_id=project_id)


@pytest.fixture(name="storage_client", scope="session")
def fixture_storage_client() -> StorageClient:
    return StorageClient()


@pytest.fixture(name="uninstantiate_teardown", scope="session")
def fixture_uninstantiate_teardown(
    model_instantiator_client: ModelInstantiatorClient,
    model_name: str,
):
    try:
        yield

    finally:
        model_instantiator_client.uninstantiate(model_name)
