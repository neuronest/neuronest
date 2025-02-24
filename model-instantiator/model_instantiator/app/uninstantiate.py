import datetime
import logging
from datetime import timedelta

from core.google.cloud_sql_manager import CloudSQLManager
from core.google.logging_client import LoggerName, LoggingClient
from core.google.vertex_ai_manager import VertexAIManager
from core.routes.model_instantiator import routes
from core.schemas.modules.model_instantiator import (
    CloudSQL,
    CloudSQLOutput,
    UninstantiateModelInput,
    UninstantiateModelLogsConditionedInput,
    UninstantiateModelOutput,
)
from core.services.deployment_status_manager import (
    DeploymentStatus,
    DeploymentStatusManager,
)
from fastapi import APIRouter, Depends, Response, status
from google.cloud import logging_v2
from omegaconf import DictConfig

from model_instantiator.app.dependencies import (
    use_cloud_sql_manager,
    use_config,
    use_deployment_status_manager,
    use_logging_client,
    use_vertex_ai_manager,
)

logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix=f"/{routes.Uninstantiator.prefix}", tags=[routes.Uninstantiator.prefix]
)


def _correctly_undeployed_endpoint_response(
    response: Response, endpoint_id: str, model_name: str
) -> UninstantiateModelOutput:
    response.status_code = status.HTTP_201_CREATED

    message = f"Endpoint '{endpoint_id}' undeployed for model_name: '{model_name}'"
    logger.info(message)

    return UninstantiateModelOutput(message=message)


def _no_endpoint_response(
    response: Response, model_name: str
) -> UninstantiateModelOutput:
    response.status_code = status.HTTP_200_OK

    message = f"No endpoint found for model_name: '{model_name}'"
    logger.info(message)

    return UninstantiateModelOutput(message=message)


def _no_traffic_response(
    response: Response, model_name: str
) -> UninstantiateModelOutput:
    response.status_code = status.HTTP_200_OK

    message = f"No traffic found for model_name: '{model_name}'"
    logger.info(message)

    return UninstantiateModelOutput(message=message)


def _too_recently_updated_endpoint_response(
    response: Response, model_name: str
) -> UninstantiateModelOutput:
    response.status_code = status.HTTP_200_OK

    message = f"Endpoint too recently updated for model_name: '{model_name}'"
    logger.warning(message)

    return UninstantiateModelOutput(message=message)


def _too_recently_used_endpoint_response(
    response: Response, model_name: str
) -> UninstantiateModelOutput:
    response.status_code = status.HTTP_200_OK

    message = f"Endpoint too recently used for model_name: '{model_name}'"
    logger.warning(message)

    return UninstantiateModelOutput(message=message)


@router.post(
    routes.Uninstantiator.uninstantiate,
    response_model=UninstantiateModelOutput,
    status_code=status.HTTP_202_ACCEPTED,
)
def uninstantiate_model(
    uninstantiate_model_input: UninstantiateModelInput,
    response: Response,
    vertex_ai_manager: VertexAIManager = Depends(use_vertex_ai_manager),
    deployment_status_manager: DeploymentStatusManager = Depends(
        use_deployment_status_manager
    ),
):
    model_name = uninstantiate_model_input.trained_model_name

    endpoint = vertex_ai_manager.get_endpoint_by_name(model_name)
    if endpoint is None:
        return _no_endpoint_response(response=response, model_name=model_name)

    model = vertex_ai_manager.get_last_model_by_name(model_name)
    if not vertex_ai_manager.is_model_deployed(endpoint=endpoint, model=model):
        return _no_traffic_response(response=response, model_name=model_name)

    endpoint.delete(force=True)
    deployment_status_manager.maybe_set_status(
        deployment_status=DeploymentStatus.UNDEPLOYED, deployment_name=model_name
    )

    return _correctly_undeployed_endpoint_response(
        response=response, endpoint_id=endpoint.resource_name, model_name=model_name
    )


@router.post(
    routes.Uninstantiator.uninstantiate_logs_conditioned,
    response_model=UninstantiateModelOutput,
    status_code=status.HTTP_202_ACCEPTED,
)
# pylint: disable=too-many-positional-arguments
def uninstantiate_model_logs_conditioned(
    uninstantiate_model_input: UninstantiateModelLogsConditionedInput,
    response: Response,
    config: DictConfig = Depends(use_config),
    vertex_ai_manager: VertexAIManager = Depends(use_vertex_ai_manager),
    deployment_status_manager: DeploymentStatusManager = Depends(
        use_deployment_status_manager
    ),
    logging_client: LoggingClient = Depends(use_logging_client),
) -> UninstantiateModelOutput:
    model_name = uninstantiate_model_input.trained_model_name
    default_messages = uninstantiate_model_input.default_messages

    endpoint = vertex_ai_manager.get_endpoint_by_name(name=model_name)
    if endpoint is None:
        return _no_endpoint_response(response=response, model_name=model_name)

    time_delta = (
        uninstantiate_model_input.time_delta_override or config.uninstantiate_time_delta
    )

    if (
        datetime.datetime.now(tz=endpoint.update_time.tzinfo) - endpoint.update_time
    ).total_seconds() < time_delta:
        return _too_recently_updated_endpoint_response(
            response=response, model_name=model_name
        )

    recent_prediction_logs = logging_client.get_filtered_logs(
        logger_name=LoggerName.PREDICTION_CONTAINER,
        date=datetime.datetime.now() - datetime.timedelta(seconds=time_delta),
        messages=default_messages + (model_name,),
    )

    if len(recent_prediction_logs) > 0:
        return _too_recently_used_endpoint_response(
            response=response, model_name=model_name
        )

    endpoint.delete(force=True)
    deployment_status_manager.set_status(
        deployment_status=DeploymentStatus.UNDEPLOYED, deployment_name=model_name
    )

    return _correctly_undeployed_endpoint_response(
        response=response,
        endpoint_id=endpoint.resource_name,
        model_name=model_name,
    )


def _no_instance_response(response: Response, instance_name: str):
    response.status_code = status.HTTP_404_NOT_FOUND

    return CloudSQLOutput(message=f"Cloud SQL instance '{instance_name}' not found")


def _already_stopped_instance_response(response: Response, instance_name: str):
    response.status_code = status.HTTP_200_OK

    return CloudSQLOutput(
        message=f"Cloud SQL instance '{instance_name}' is already stopped"
    )


def _correctly_stopped_instance_response(response: Response, instance_name: str):
    response.status_code = status.HTTP_202_ACCEPTED

    return CloudSQLOutput(
        message=f"Cloud SQL instance '{instance_name}' has been successfully stopped"
    )


def _too_recently_used_cloud_sql_instance_response(
    response: Response, instance_name: str, status_code: int = status.HTTP_200_OK
):
    response.status_code = status_code

    return CloudSQLOutput(
        message=f"CloudSQL instance '{instance_name}' too recently used"
    )


def _uninstantiate_cloud_sql_instance(
    cloud_sql_name: str,
    response: Response,
    cloud_sql_manager: CloudSQLManager,
):
    # Check if the instance exists
    cloud_sql_instance = cloud_sql_manager.get_instance_by_name(cloud_sql_name)
    if cloud_sql_instance is None:
        return _no_instance_response(response=response, instance_name=cloud_sql_name)

    # Check if the instance is already stopped
    if cloud_sql_manager.is_instance_stopped(instance_name=cloud_sql_name):
        return _already_stopped_instance_response(
            response=response, instance_name=cloud_sql_name
        )

    # Stop the Cloud SQL instance
    cloud_sql_manager.stop_instance(instance_name=cloud_sql_name, sync=True)

    return _correctly_stopped_instance_response(
        response=response,
        instance_name=cloud_sql_name,
    )


@router.post(
    routes.Uninstantiator.cloud_sql_uninstantiate,
    response_model=CloudSQLOutput,
    status_code=status.HTTP_202_ACCEPTED,
)
def uninstantiate_cloud_sql_instance(
    uninstantiate_cloud_sql_input: CloudSQL,
    response: Response,
    cloud_sql_manager: CloudSQLManager = Depends(use_cloud_sql_manager),
):

    return _uninstantiate_cloud_sql_instance(
        cloud_sql_name=uninstantiate_cloud_sql_input.instance_name,
        response=response,
        cloud_sql_manager=cloud_sql_manager,
    )


def _instance_still_starting_response(
    response: Response, instance_name: str, status_code: int = status.HTTP_200_OK
):

    response.status_code = status_code
    return CloudSQLOutput(
        message=f"Cloud SQL instance '{instance_name}' "
        f"is still starting and cannot be uninstantiated yet."
    )


def _already_stopping_instance_response(response: Response, instance_name: str):

    response.status_code = status.HTTP_200_OK
    return CloudSQLOutput(
        message=f"Cloud SQL instance '{instance_name}' is already stopping."
    )


def _too_recently_started_cloud_sql_instance_response(
    response: Response,
    instance_name: str,
    response_status_code: int = status.HTTP_200_OK,
):

    response.status_code = response_status_code
    return CloudSQLOutput(
        message=f"Cloud SQL instance '{instance_name}' "
        f"has started too recently and cannot be uninstantiated yet."
    )


@router.post(
    routes.Uninstantiator.cloud_sql_uninstantiate_logs_conditioned,
    status_code=status.HTTP_202_ACCEPTED,
)
def uninstantiate_cloud_sql_usage_conditioned(
    uninstantiate_cloud_sql_input: CloudSQL,
    response: Response,
    config: DictConfig = Depends(use_config),
    cloud_sql_manager: CloudSQLManager = Depends(use_cloud_sql_manager),
    logging_client: LoggingClient = Depends(use_logging_client),
):
    instance_name = uninstantiate_cloud_sql_input.instance_name
    logging.info(
        f"Received request to uninstantiate Cloud SQL instance: {instance_name}"
    )

    # Check if the instance is still starting
    if cloud_sql_manager.is_instance_starting(instance_name):
        logging.info(
            f"Instance {instance_name} is still starting. Skipping uninstantiation."
        )
        return _instance_still_starting_response(
            response=response, instance_name=instance_name
        )

    # Check if the instance is already stopping
    if cloud_sql_manager.is_instance_stopping(instance_name):
        logging.info(
            f"Instance {instance_name} is already stopping. No further action required."
        )
        return _already_stopping_instance_response(
            response=response, instance_name=instance_name
        )

    # Check if the instance is already stopped
    if cloud_sql_manager.is_instance_stopped(instance_name):
        logging.info(
            f"Instance {instance_name} is already stopped. No further action required."
        )
        return _already_stopped_instance_response(
            response=response, instance_name=instance_name
        )

    # Check how long the instance has been running
    instance_last_started_time = cloud_sql_manager.get_instance_last_update_end_time(
        instance_name
    )
    required_time_to_uninstantiate = timedelta(
        seconds=config.uninstantiate_cloud_sql_time_delta
    )
    time_running = datetime.datetime.utcnow() - instance_last_started_time

    if time_running < required_time_to_uninstantiate:
        logging.info(
            f"Instance {instance_name} has been running for {time_running}, "
            f"which is less than required {required_time_to_uninstantiate}."
            f" Skipping uninstantiation."
        )
        return _too_recently_started_cloud_sql_instance_response(
            response=response, instance_name=instance_name
        )

    # Define the time window for checking logs
    instance_active_check_start_time = (
        datetime.datetime.utcnow() - required_time_to_uninstantiate
    )
    logging.info(
        f"Checking logs for non-cloudsqladmin queries "
        f"since {instance_active_check_start_time.isoformat()}Z"
    )

    # Query logs for non-cloudsqladmin activity
    # Using a large page_size to reduce the number of API requests.
    # Setting page_size too small could result in multiple requests,
    # increasing the risk of exceeding quota limits due to high request volumes.

    non_cloudsqladmin_queries_logs = [
        log
        for log in list(
            logging_client.client.list_entries(
                filter_=f"""
                        resource.type="cloudsql_database"
                        resource.labels.database_id="{logging_client.project_id}:{instance_name}"
                        textPayload:"statement:"
                        timestamp >= "{instance_active_check_start_time.isoformat()}Z"
                        """,
                order_by=logging_v2.DESCENDING,
                # Using a very large page_size to minimize the number of API calls.
                # Frequent calls due to smaller page_size can trigger quota violations.
                page_size=1_000_000_000,
            )
        )
        if "user=cloudsqladmin" not in log.payload
    ]

    # If non-cloudsqladmin activity is detected, do not stop the instance
    if non_cloudsqladmin_queries_logs:
        logging.info(
            f"Recent queries found by non-cloudsqladmin users on {instance_name}."
            f" Keeping instance running."
        )
        return _too_recently_used_cloud_sql_instance_response(
            response=response,
            instance_name=instance_name,
            status_code=status.HTTP_200_OK,
        )

    # If no recent activity is detected, proceed to stop the instance
    logging.info(
        f"No recent non-cloudsqladmin activity detected. "
        f"Stopping instance {instance_name}."
    )
    return _uninstantiate_cloud_sql_instance(
        cloud_sql_name=instance_name,
        response=response,
        cloud_sql_manager=cloud_sql_manager,
    )
