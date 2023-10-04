import os
from typing import Optional

import pytest
from core.client.model_instantiator import ModelInstantiatorClient
from core.client.people_counting import PeopleCountingClient
from core.google.storage_client import StorageClient


@pytest.fixture(name="model_instantiator_host")
def fixture_model_instantiator_host() -> str:
    return os.environ["MODEL_INSTANTIATOR_HOST"]


@pytest.fixture(name="people_counting_url")
def fixture_people_counting_url() -> str:
    return os.environ["PEOPLE_COUNTING_URL"]


@pytest.fixture(name="project_id")
def fixture_project_id() -> str:
    return os.environ["PROJECT_ID"]


@pytest.fixture(name="model_name")
def fixture_model_name() -> str:
    return os.environ["MODEL_NAME"]


@pytest.fixture(name="google_application_credentials")
def fixture_google_application_credentials() -> Optional[str]:
    return os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")


@pytest.fixture(name="model_instantiator_client")
def fixture_model_instantiator_client(
    model_instantiator_host: str,
) -> ModelInstantiatorClient:
    return ModelInstantiatorClient(
        host=model_instantiator_host,
    )


@pytest.fixture(name="people_counting_client")
def fixture_people_counting_client(
    people_counting_url: str, project_id: str
) -> PeopleCountingClient:
    return PeopleCountingClient(host=people_counting_url, project_id=project_id)


@pytest.fixture(name="storage_client")
def fixture_storage_client() -> StorageClient:
    return StorageClient()
