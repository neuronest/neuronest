import os

from core.exceptions import AlreadyExistingError
from core.google.vertex_ai_manager import VertexAIManager
from core.schemas.model_instantiator import (
    InstantiateModelInput,
    InstantiateModelOutput,
)
from core.schemas.vertex_ai import ServingDeploymentConfig
from fastapi import APIRouter, Depends, Response
from omegaconf import DictConfig
from omegaconf.errors import ConfigAttributeError
from starlette import status

from model_instantiator.api.dependencies import use_config, use_vertex_ai_manager
from model_instantiator.config import cfg

router = APIRouter(tags=[os.path.splitext(os.path.basename(__file__))[0]])


def _correctly_deployed_endpoint_response(
    response: Response, model_name: str
) -> InstantiateModelOutput:
    response.status_code = status.HTTP_201_CREATED

    return InstantiateModelOutput(
        message=f"Endpoint being deployed for model_name: '{model_name}'"
    )


def _no_serving_deployment_response(
    response: Response, model_name: str
) -> InstantiateModelOutput:
    response.status_code = status.HTTP_404_NOT_FOUND

    return InstantiateModelOutput(
        message=f"No serving_deployment configuration found for model with name: "
        f"'{model_name}'"
    )


def _no_model_response(response: Response, model_name: str) -> InstantiateModelOutput:
    response.status_code = status.HTTP_404_NOT_FOUND

    return InstantiateModelOutput(
        message=f"No vertex model found with name: '{model_name}'"
    )


def _already_deployed_model_response(
    response: Response, model_name: str
) -> InstantiateModelOutput:
    response.status_code = status.HTTP_409_CONFLICT

    return InstantiateModelOutput(
        message=f"The model '{model_name}' is already deployed"
    )


@router.post(cfg.routes.instantiate, status_code=status.HTTP_201_CREATED)
def instantiate_model(
    instantiate_model_input: InstantiateModelInput,
    response: Response,
    config: DictConfig = Depends(use_config),
    vertex_ai_manager: VertexAIManager = Depends(use_vertex_ai_manager),
):
    model_name = instantiate_model_input.model_name

    try:
        raw_serving_deployment_config = getattr(config.serving_deployment, model_name)
    except ConfigAttributeError:
        return _no_serving_deployment_response(response=response, model_name=model_name)

    serving_deployment_config = ServingDeploymentConfig.parse_obj(
        raw_serving_deployment_config
    )
    model = vertex_ai_manager.get_last_model_by_name(name=model_name)

    if model is None:
        return _no_model_response(response=response, model_name=model_name)

    try:
        vertex_ai_manager.deploy_model(
            name=model_name,
            model=model,
            serving_deployment_config=serving_deployment_config,
            sync=False,
        )
    except AlreadyExistingError:
        return _already_deployed_model_response(
            response=response, model_name=model_name
        )

    return _correctly_deployed_endpoint_response(
        response=response, model_name=model_name
    )
