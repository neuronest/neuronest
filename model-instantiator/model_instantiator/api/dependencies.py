from functools import lru_cache

from core.google.firestore_client import FirestoreClient
from core.google.logging_client import LoggingClient
from core.google.vertex_ai_manager import VertexAIManager
from core.services.deployment_status_manager import DeploymentStatusManager
from fastapi import Depends
from omegaconf import DictConfig

from model_instantiator.config import cfg
from model_instantiator.environment_variables import (
    GOOGLE_APPLICATION_CREDENTIALS,
    PROJECT_ID,
)


@lru_cache()
def use_config() -> DictConfig:
    return cfg


@lru_cache
def use_vertex_ai_manager(config: DictConfig = Depends(use_config)) -> VertexAIManager:
    return VertexAIManager(
        location=config.region,
        key_path=GOOGLE_APPLICATION_CREDENTIALS,
        project_id=PROJECT_ID,
    )


@lru_cache
def use_firestore_client() -> FirestoreClient:
    return FirestoreClient(
        key_path=GOOGLE_APPLICATION_CREDENTIALS,
    )


@lru_cache
def use_deployment_status_manager(
    config: DictConfig = Depends(use_config),
    firestore_client: FirestoreClient = Depends(use_firestore_client),
) -> DeploymentStatusManager:
    return DeploymentStatusManager(
        firestore_client=firestore_client,
        collection_name=config.firestore.deployment_status_collection_name,
        max_deploying_age=config.max_deploying_age,
    )


@lru_cache
def use_logging_client() -> LoggingClient:
    return LoggingClient(key_path=GOOGLE_APPLICATION_CREDENTIALS)
