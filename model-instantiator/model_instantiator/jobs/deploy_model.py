from typing import Optional

from core.google.cloud_scheduler import CloudSchedulerManager
from core.google.vertex_ai_manager import VertexAIManager
from core.schemas.vertex_ai import ServingDeploymentConfig
from core.services.deployment_status_manager import (
    DeploymentStatus,
    DeploymentStatusManager,
)
from google.cloud import aiplatform

from model_instantiator.config import cfg
from model_instantiator.jobs.environment_variables import (
    CLOUD_SCHEDULER_JOB_NAME,
    IS_LAST_MODEL_ALREADY_DEPLOYED_OK,
    MODEL_NAME,
    UNDEPLOY_PREVIOUS_MODEL,
)
from model_instantiator.jobs.services import (
    create_cloud_scheduler_manager,
    create_deployment_status_manager,
    create_firestore_client,
    create_vertex_ai_manager,
)


def deploy_model(
    model_name: str,
    deployment_status_manager: DeploymentStatusManager,
    vertex_ai_manager: VertexAIManager,
    cloud_scheduler_manager: CloudSchedulerManager,
    cloud_scheduler_job_name: str,
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

    if vertex_ai_manager.is_model_deployed(
        endpoint=endpoint,
        model=model,
    ):
        cloud_scheduler_manager.resume_job(job_name=cloud_scheduler_job_name)
        deployment_status_manager.set_status(
            deployment_status=DeploymentStatus.DEPLOYED, deployment_name=model_name
        )

        return endpoint

    deployment_status_manager.set_status(
        deployment_status=DeploymentStatus.FAILED, deployment_name=model_name
    )

    return None


if __name__ == "__main__":
    firestore_client = create_firestore_client()

    deploy_model(
        model_name=MODEL_NAME,
        deployment_status_manager=create_deployment_status_manager(
            config=cfg, firestore_client=firestore_client
        ),
        vertex_ai_manager=create_vertex_ai_manager(),
        cloud_scheduler_manager=create_cloud_scheduler_manager(),
        cloud_scheduler_job_name=CLOUD_SCHEDULER_JOB_NAME,
        undeploy_previous_model=UNDEPLOY_PREVIOUS_MODEL,
        is_last_model_already_deployed_ok=IS_LAST_MODEL_ALREADY_DEPLOYED_OK,
    )
