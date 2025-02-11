from typing import Optional

import pytest
from core.client.database_api import DatabaseApiClient
from core.client.model_instantiator import ModelInstantiatorClient

from tests.environment_variables import (
    CLOUD_SQL_INSTANCE_NAME,
    DATABASE_API_HOST,
    GOOGLE_APPLICATION_CREDENTIALS,
    MODEL_INSTANTIATOR_HOST,
)


@pytest.fixture(name="google_application_credentials", scope="session")
def fixture_google_application_credentials() -> Optional[str]:
    return GOOGLE_APPLICATION_CREDENTIALS


@pytest.fixture(name="database_api_host", scope="session")
def fixture_database_api_host() -> str:
    return DATABASE_API_HOST


@pytest.fixture(name="cloud_sql_instance_name", scope="session")
def fixture_cloud_sql_instance_name() -> str:
    return CLOUD_SQL_INSTANCE_NAME


# @pytest.fixture(name="project_id", scope="session")
# def fixture_project_id() -> str:
#     return PROJECT_ID


@pytest.fixture(name="model_instantiator_host", scope="session")
def fixture_model_instantiator_host() -> str:
    return MODEL_INSTANTIATOR_HOST


@pytest.fixture(name="model_instantiator_client", scope="session")
def fixture_model_instantiator_client(
    model_instantiator_host: str, google_application_credentials: Optional[str]
) -> ModelInstantiatorClient:
    return ModelInstantiatorClient(
        host=model_instantiator_host,
        key_path=google_application_credentials,
    )


@pytest.fixture(name="database_api_client", scope="session")
def fixture_database_api_client(
    database_api_host: str,
):
    return DatabaseApiClient(
        host=database_api_host,
    )


@pytest.fixture(name="uninstantiate_teardown", scope="session")
def fixture_uninstantiate_teardown(
    # pylint: disable=unused-argument
    model_instantiator_client: ModelInstantiatorClient,
    # pylint: disable=unused-argument
    cloud_sql_instance_name: str,
):
    try:
        yield

    finally:
        pass
        # model_instantiator_client.uninstantiate_cloud_sql(cloud_sql_instance_name)
