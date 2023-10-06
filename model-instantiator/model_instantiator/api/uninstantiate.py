import datetime
import logging
import os

from core.google.logging_client import LoggerName, LoggingClient
from core.google.vertex_ai_manager import VertexAIManager
from core.routes.model_instantiator import route
from core.schemas.model_instantiator import (
    UninstantiateModelInput,
    UninstantiateModelLogsConditionedInput,
    UninstantiateModelOutput,
)
from core.services.deployment_status_manager import (
    DeploymentStatus,
    DeploymentStatusManager,
)
from fastapi import APIRouter, Depends, Response
from omegaconf import DictConfig
from starlette import status

from model_instantiator.api.dependencies import (
    use_config,
    use_deployment_status_manager,
    use_logging_client,
    use_vertex_ai_manager,
)

logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)

router = APIRouter(tags=[os.path.splitext(os.path.basename(__file__))[0]])


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
    route.uninstantiate,
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
    model_name = uninstantiate_model_input.model_name

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
    route.uninstantiate_logs_conditioned,
    response_model=UninstantiateModelOutput,
    status_code=status.HTTP_202_ACCEPTED,
)
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
    model_name = uninstantiate_model_input.model_name
    default_messages = uninstantiate_model_input.default_messages

    endpoint = vertex_ai_manager.get_endpoint_by_name(model_name)
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
