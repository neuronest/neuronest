import pytest
from core.client.database_api import DatabaseApiClient
from core.client.model_instantiator import ModelInstantiatorClient

from tests.environment_variables import (
    CLOUD_SQL_INSTANCE_NAME,
    DATABASE_API_HOST,
    MODEL_INSTANTIATOR_HOST,
)


@pytest.fixture(name="database_api_host", scope="session")
def fixture_database_api_host() -> str:
    return DATABASE_API_HOST


@pytest.fixture(name="cloud_sql_instance_name", scope="session")
def fixture_cloud_sql_instance_name() -> str:
    return CLOUD_SQL_INSTANCE_NAME


@pytest.fixture(name="model_instantiator_host", scope="session")
def fixture_model_instantiator_host() -> str:
    return MODEL_INSTANTIATOR_HOST


@pytest.fixture(name="model_instantiator_client", scope="session")
def fixture_model_instantiator_client(
    model_instantiator_host: str,
) -> ModelInstantiatorClient:
    return ModelInstantiatorClient(host=model_instantiator_host)


@pytest.fixture(name="database_api_client", scope="session")
def fixture_database_api_client(
    database_api_host: str,
):
    return DatabaseApiClient(host=database_api_host)
