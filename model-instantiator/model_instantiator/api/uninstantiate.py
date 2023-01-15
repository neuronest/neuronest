import datetime
import os

from core.google.logging_client import LoggerName, LoggingClient
from core.google.vertex_ai_manager import VertexAIManager
from core.schemas.model_instantiator import (
    PubSubUninstantiateModelLogsConditioned,
    UninstantiateModelInput,
    UninstantiateModelLogsConditionedInput,
    UninstantiateModelOutput,
)
from fastapi import APIRouter, Depends, Response
from omegaconf import DictConfig
from starlette import status

from model_instantiator.api.dependencies import (
    use_config,
    use_logging_client,
    use_vertex_ai_manager,
)
from model_instantiator.config import cfg

router = APIRouter(tags=[os.path.splitext(os.path.basename(__file__))[0]])


def _correctly_undeployed_endpoint_response(
    response: Response, endpoint_id: str, model_name: str
) -> UninstantiateModelOutput:
    response.status_code = status.HTTP_202_ACCEPTED

    return UninstantiateModelOutput(
        message=f"Endpoint '{endpoint_id}' undeployed for model_name: "
        f"'{model_name}'"
    )


def _no_endpoint_response(
    response: Response, model_name: str
) -> UninstantiateModelOutput:
    response.status_code = status.HTTP_404_NOT_FOUND

    return UninstantiateModelOutput(
        message=f"No endpoint found for model_name: '{model_name}'"
    )


def _too_recently_updated_endpoint_response(
    response: Response, model_name: str
) -> UninstantiateModelOutput:
    response.status_code = status.HTTP_400_BAD_REQUEST

    return UninstantiateModelOutput(
        message=f"Endpoint too recently updated for model_name: '{model_name}'"
    )


def _too_recently_used_endpoint_response(
    response: Response, model_name: str
) -> UninstantiateModelOutput:
    response.status_code = status.HTTP_400_BAD_REQUEST

    return UninstantiateModelOutput(
        message=f"Endpoint too recently used for model_name: '{model_name}'"
    )


@router.post(
    cfg.routes.uninstantiate,
    response_model=UninstantiateModelOutput,
    status_code=status.HTTP_202_ACCEPTED,
)
def uninstantiate_model(
    uninstantiate_model_input: UninstantiateModelInput,
    response: Response,
    vertex_ai_manager: VertexAIManager = Depends(use_vertex_ai_manager),
):
    model_name = uninstantiate_model_input.model_name

    endpoint = vertex_ai_manager.get_last_endpoint_by_name(model_name)
    if endpoint is None:
        return _no_endpoint_response(response=response, model_name=model_name)

    endpoint.delete(force=True)

    return _correctly_undeployed_endpoint_response(
        response=response, endpoint_id=endpoint.resource_name, model_name=model_name
    )


def _uninstantiate_model_logs_conditioned(
    uninstantiate_model_input: UninstantiateModelLogsConditionedInput,
    response: Response,
    vertex_ai_manager: VertexAIManager,
    logging_client: LoggingClient,
    uninstantiate_time_delta: int,
):
    model_name = uninstantiate_model_input.model_name
    default_messages = uninstantiate_model_input.default_messages

    endpoint = vertex_ai_manager.get_last_endpoint_by_name(model_name)
    if endpoint is None:
        return _no_endpoint_response(response=response, model_name=model_name)

    time_delta = (
        uninstantiate_model_input.time_delta_override or uninstantiate_time_delta
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

    return _correctly_undeployed_endpoint_response(
        response=response,
        endpoint_id=endpoint.resource_name,
        model_name=model_name,
    )


@router.post(
    cfg.routes.uninstantiate_logs_conditioned,
    response_model=UninstantiateModelOutput,
    status_code=status.HTTP_202_ACCEPTED,
)
def uninstantiate_model_logs_conditioned(
    uninstantiate_model_input: UninstantiateModelLogsConditionedInput,
    response: Response,
    config: DictConfig = Depends(use_config),
    vertex_ai_manager: VertexAIManager = Depends(use_vertex_ai_manager),
    logging_client: LoggingClient = Depends(use_logging_client),
) -> UninstantiateModelOutput:
    return _uninstantiate_model_logs_conditioned(
        uninstantiate_model_input=uninstantiate_model_input,
        response=response,
        vertex_ai_manager=vertex_ai_manager,
        logging_client=logging_client,
        uninstantiate_time_delta=config.uninstantiate_time_delta,
    )


@router.post(
    cfg.routes.pubsub_uninstantiate_logs_conditioned,
    response_model=UninstantiateModelOutput,
    status_code=status.HTTP_202_ACCEPTED,
)
def pubsub_uninstantiate_model_logs_conditioned(
    pubsub_message: PubSubUninstantiateModelLogsConditioned,
    response: Response,
    config: DictConfig = Depends(use_config),
    vertex_ai_manager: VertexAIManager = Depends(use_vertex_ai_manager),
    logging_client: LoggingClient = Depends(use_logging_client),
) -> UninstantiateModelOutput:
    return _uninstantiate_model_logs_conditioned(
        uninstantiate_model_input=pubsub_message.data,
        response=response,
        vertex_ai_manager=vertex_ai_manager,
        logging_client=logging_client,
        uninstantiate_time_delta=config.uninstantiate_time_delta,
    )
