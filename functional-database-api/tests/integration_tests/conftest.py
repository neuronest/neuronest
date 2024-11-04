from typing import Optional

import pytest
from core.client.database_api import DatabaseApiClient
from core.client.model_instantiator import ModelInstantiatorClient

from tests.environment_variables import (
    CLOUD_SQL_CONNECTION_NAME,
    DATABASE_API_HOST,
    GOOGLE_APPLICATION_CREDENTIALS,
    PROJECT_ID,
    REGION,
)


@pytest.fixture(name="google_application_credentials", scope="session")
def fixture_google_application_credentials() -> Optional[str]:
    return GOOGLE_APPLICATION_CREDENTIALS


@pytest.fixture(name="model_instantiator_host", scope="session")
def fixture_database_api_host() -> str:
    return DATABASE_API_HOST


@pytest.fixture(name="model_name", scope="session")
def fixture_cloud_sql_connection_name() -> str:
    return CLOUD_SQL_CONNECTION_NAME


@pytest.fixture(name="project_id", scope="session")
def fixture_project_id() -> str:
    return PROJECT_ID


@pytest.fixture(name="region", scope="session")
def fixture_region() -> str:
    return REGION


@pytest.fixture(name="model_instantiator_client", scope="session")
def fixture_model_instantiator_client(
    model_instantiator_host: str, google_application_credentials: Optional[str]
) -> ModelInstantiatorClient:
    return ModelInstantiatorClient(
        host=model_instantiator_host,
        key_path=google_application_credentials,
    )


@pytest.fixture(name="object_detection_client", scope="session")
def fixture_database_api_client(
    database_api_host: str,
):
    return DatabaseApiClient(
        host=database_api_host,
    )


@pytest.fixture(name="uninstantiate_teardown", scope="session")
def fixture_uninstantiate_teardown(
    model_instantiator_client: ModelInstantiatorClient,
    cloud_sql_connection_name: str,
):
    try:
        yield

    finally:
        model_instantiator_client.uninstantiate_cloud_sql(cloud_sql_connection_name)
