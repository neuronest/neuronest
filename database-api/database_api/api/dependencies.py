import logging
from functools import lru_cache

from core.client.model_instantiator import ModelInstantiatorClient
from core.google.cloud_sql_manager import CloudSQLManager

from database_api.api.exceptions import (
    DatabaseStartingError,
    DatabaseStoppedError,
    DatabaseStoppingError,
)
from database_api.database import SessionLocal
from database_api.environment_variables import INSTANCE_NAME, MODEL_INSTANTIATOR_HOST

# Configure logging
logging.basicConfig(level=logging.INFO)


@lru_cache
def get_cloud_sql_manager() -> CloudSQLManager:
    return CloudSQLManager()


@lru_cache
def get_model_instantiator_client() -> ModelInstantiatorClient:
    return ModelInstantiatorClient(host=MODEL_INSTANTIATOR_HOST)


def handle_potential_cloud_sql_error(
    raise_error: bool = False,
    on_error_correct: bool = False,
):
    """
    Handles Cloud SQL instance errors by checking the instance state and
    raising appropriate exceptions if needed.

    Parameters:
        raise_error (bool): Whether to raise an exception when an error is detected.
        on_error_correct (bool): Whether to attempt correcting the detected error.

    Returns:
        None or Exception: Returns the error if raise_error is False,
        otherwise raises the error.
    """

    cloud_sql_manager = get_cloud_sql_manager()
    error = None

    if cloud_sql_manager.is_instance_stopped(INSTANCE_NAME):
        error = DatabaseStoppedError

    if cloud_sql_manager.is_instance_stopping(INSTANCE_NAME):
        error = DatabaseStoppingError

    if cloud_sql_manager.is_instance_starting(INSTANCE_NAME):
        error = DatabaseStartingError

    if on_error_correct and error in (DatabaseStoppedError, DatabaseStoppingError):
        logging.info(f"Attempting to restart Cloud SQL instance: {INSTANCE_NAME}")
        get_model_instantiator_client().instantiate_cloud_sql(INSTANCE_NAME)

    if error is DatabaseStartingError:
        logging.info(
            f"Cloud SQL instance '{INSTANCE_NAME}' is in the process of starting. "
            f"Waiting is required."
        )

    if error is None:
        return None

    if raise_error:
        logging.critical(
            f"Raising exception due to Cloud SQL instance issue: {error.__name__}"
        )
        raise error(f"Cloud SQL instance issue: {INSTANCE_NAME}")

    return error


def get_database():
    """
    Dependency to manage the database session lifecycle
    and handle Cloud SQL instance errors.
    """
    database = SessionLocal()
    try:
        yield database
    except Exception as exception:
        handle_potential_cloud_sql_error(raise_error=True)
        raise exception

    finally:
        database.close()
