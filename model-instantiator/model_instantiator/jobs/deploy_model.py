from typing import Optional

from core.google.vertex_ai_manager import VertexAIManager
from core.schemas.vertex_ai import ServingDeploymentConfig
from core.services.deployment_status_manager import (
    DeploymentStatus,
    DeploymentStatusManager,
)
from google.cloud import aiplatform

from model_instantiator.api.dependencies import (
    use_config,
    use_deployment_status_manager,
    use_firestore_client,
    use_vertex_ai_manager,
)
from model_instantiator.jobs.environment_variables import (
    IS_LAST_MODEL_ALREADY_DEPLOYED_OK,
    MODEL_NAME,
    UNDEPLOY_PREVIOUS_MODEL,
)


def deploy_model(
    model_name: str,
    deployment_status_manager: DeploymentStatusManager,
    vertex_ai_manager: VertexAIManager,
    undeploy_previous_model: bool,
    is_last_model_already_deployed_ok: bool,
) -> Optional[aiplatform.Endpoint]:
    model = vertex_ai_manager.get_last_model_by_name(name=model_name)
    serving_deployment_config = ServingDeploymentConfig.from_labels(model.labels)

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


if __name__ == "__main__":
    config = use_config()
    firestore_client = use_firestore_client()

    deploy_model(
        model_name=MODEL_NAME,
        deployment_status_manager=use_deployment_status_manager(
            config=config, firestore_client=firestore_client
        ),
        vertex_ai_manager=use_vertex_ai_manager(config=config),
        undeploy_previous_model=UNDEPLOY_PREVIOUS_MODEL,
        is_last_model_already_deployed_ok=IS_LAST_MODEL_ALREADY_DEPLOYED_OK,
    )
