from core.google.firestore_client import FirestoreClient
from core.google.vertex_ai_manager import VertexAIManager
from core.services.deployment_status_manager import DeploymentStatusManager
from omegaconf import DictConfig

from model_instantiator.jobs.environment_variables import PROJECT_ID, VERTEX_LOCATION


def create_vertex_ai_manager() -> VertexAIManager:
    return VertexAIManager(location=VERTEX_LOCATION, project_id=PROJECT_ID)


def create_firestore_client() -> FirestoreClient:
    return FirestoreClient(
        project_id=PROJECT_ID,
    )


def create_deployment_status_manager(
    config: DictConfig,
    firestore_client: FirestoreClient,
) -> DeploymentStatusManager:
    return DeploymentStatusManager(
        firestore_client=firestore_client,
        collection_name=config.firestore.deployment_status_collection_name,
        max_deploying_age=config.max_deploying_age,
    )
