import os
from typing import Optional

from core.google.vertex_ai_manager import VertexAIManager
from core.schemas.model_instantiator import (
    InstantiateModelInput,
    InstantiateModelOutput,
)
from core.schemas.vertex_ai import ServingDeploymentConfig
from core.services.deployment_status_manager import (
    DeploymentStatus,
    DeploymentStatusManager,
)
from fastapi import APIRouter, BackgroundTasks, Depends, Response
from google.cloud import aiplatform
from starlette import status

from model_instantiator.api.dependencies import (
    use_deployment_status_manager,
    use_vertex_ai_manager,
)
from model_instantiator.config import cfg

router = APIRouter(tags=[os.path.splitext(os.path.basename(__file__))[0]])


def _already_deployed_endpoint_response(
    response: Response, model_name: str
) -> InstantiateModelOutput:
    response.status_code = status.HTTP_200_OK

    return InstantiateModelOutput(
        message=f"Endpoint already deployed for model_name: '{model_name}'"
    )


def _deploying_endpoint_response(
    response: Response, model_name: str
) -> InstantiateModelOutput:
    response.status_code = status.HTTP_201_CREATED

    return InstantiateModelOutput(
        message=f"Endpoint being deployed for model_name: '{model_name}', "
        f"or is already deploying"
    )


def _no_model_response(response: Response, model_name: str) -> InstantiateModelOutput:
    response.status_code = status.HTTP_404_NOT_FOUND

    return InstantiateModelOutput(
        message=f"No vertex model found with name: '{model_name}'"
    )


def deploy_model(
    model_name: str,
    deployment_status_manager: DeploymentStatusManager,
    vertex_ai_manager: VertexAIManager,
    model: aiplatform.Model,
    serving_deployment_config: ServingDeploymentConfig,
    undeploy_previous_model: bool = True,
    is_last_model_already_deployed_ok: bool = False,
) -> Optional[aiplatform.Endpoint]:
    deployment_status_document = deployment_status_manager.maybe_set_status(
        deployment_status=DeploymentStatus.DEPLOYING, deployment_name=model_name
    )
    has_status_been_changed = deployment_status_document is not None

    if not has_status_been_changed:
        return None

    endpoint = vertex_ai_manager.deploy_model(
        name=model_name,
        model=model,
        serving_deployment_config=serving_deployment_config,
        undeploy_previous_model=undeploy_previous_model,
        is_last_model_already_deployed_ok=is_last_model_already_deployed_ok,
        timeout=deployment_status_manager.max_deploying_age,
    )

    if vertex_ai_manager.is_model_deployed(endpoint=endpoint, model=model):
        deployment_status_manager.set_status(
            deployment_status=DeploymentStatus.DEPLOYED, deployment_name=model_name
        )

        return endpoint

    deployment_status_manager.set_status(
        deployment_status=DeploymentStatus.FAILED, deployment_name=model_name
    )

    return None


@router.post(cfg.routes.instantiate, status_code=status.HTTP_201_CREATED)
def instantiate_model(
    instantiate_model_input: InstantiateModelInput,
    background_tasks: BackgroundTasks,
    response: Response,
    deployment_status_manager: DeploymentStatusManager = Depends(
        use_deployment_status_manager
    ),
    vertex_ai_manager: VertexAIManager = Depends(use_vertex_ai_manager),
):
    model_name = instantiate_model_input.model_name

    model = vertex_ai_manager.get_model_by_name(name=model_name)

    if model is None:
        return _no_model_response(response=response, model_name=model_name)

    serving_deployment_config = ServingDeploymentConfig.from_labels(model.labels)

    if vertex_ai_manager.is_model_deployed(name=model_name, model=model):
        deployment_status_manager.maybe_set_status(
            deployment_status=DeploymentStatus.DEPLOYED, deployment_name=model_name
        )

        return _already_deployed_endpoint_response(
            response=response, model_name=model_name
        )

    background_tasks.add_task(
        deploy_model,
        model_name=model_name,
        deployment_status_manager=deployment_status_manager,
        vertex_ai_manager=vertex_ai_manager,
        model=model,
        serving_deployment_config=serving_deployment_config,
    )

    return _deploying_endpoint_response(response=response, model_name=model_name)
