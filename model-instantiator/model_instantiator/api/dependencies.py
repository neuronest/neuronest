from functools import lru_cache

from core.google.logging_client import LoggingClient
from core.google.vertex_ai_manager import VertexAIManager
from fastapi import Depends
from omegaconf import DictConfig

from model_instantiator.config import cfg
from model_instantiator.environment_variables import GOOGLE_APPLICATION_CREDENTIALS


@lru_cache()
def use_config() -> DictConfig:
    return cfg


@lru_cache
def use_vertex_ai_manager(config: DictConfig = Depends(use_config)) -> VertexAIManager:
    return VertexAIManager(
        key_path=GOOGLE_APPLICATION_CREDENTIALS, location=config.region
    )


@lru_cache
def use_logging_client() -> LoggingClient:
    return LoggingClient(key_path=GOOGLE_APPLICATION_CREDENTIALS)
