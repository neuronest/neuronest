import time
from abc import ABC, abstractmethod
from typing import Any, List, Optional

import requests
from cachetools.func import ttl_cache
from google.cloud import aiplatform

from core.client.base_client import BaseClient
from core.client.model_instantiator import ModelInstantiatorClient
from core.exceptions import DependencyError
from core.google.vertex_ai_manager import VertexAIManager


class OnlinePredictionModelClient(BaseClient, ABC):
    def __init__(
        self,
        vertex_ai_manager: VertexAIManager,
        model_instantiator_client: ModelInstantiatorClient,
        model_name: str,
        endpoint_retry_wait_time: int = 30,
        endpoint_retry_timeout: int = 2700,
        key_path: Optional[str] = None,
        project_id: Optional[str] = None,
    ):
        super().__init__(key_path=key_path, project_id=project_id)
        self.vertex_ai_manager = vertex_ai_manager
        self.model_instantiator_client = model_instantiator_client
        self.model_name = model_name
        self.endpoint_retry_wait_time = endpoint_retry_wait_time
        self.endpoint_retry_timeout = endpoint_retry_timeout

    def _create_endpoint(self) -> Optional[requests.Response]:
        return self.model_instantiator_client.instantiate(self.model_name)

    @ttl_cache(ttl=600)
    def _try_get_endpoint(self) -> aiplatform.Endpoint:
        total_waited_time = 0

        while total_waited_time < self.endpoint_retry_timeout:
            # todo: the function says that it returns the endpoint but only returns the
            #  endpoint if it is the last model which is deployed at the endpoint. At a
            #  minimum rename the function so that you don't have to know the
            #  implementation to know what it does
            #  e.g _try_get_latest_model_deployed_endpoint

            last_model = self.vertex_ai_manager.get_last_model_by_name(self.model_name)
            endpoint = self.vertex_ai_manager.get_endpoint_by_name(self.model_name)

            if endpoint is not None and self.vertex_ai_manager.is_model_deployed(
                model=last_model, endpoint=endpoint
            ):
                return endpoint

            self._create_endpoint()
            time.sleep(self.endpoint_retry_wait_time)
            total_waited_time += self.endpoint_retry_wait_time

        raise DependencyError(
            f"Failed to deploy an endpoint for model_name={self.model_name}, "
            f"giving up after {self.endpoint_retry_timeout // 60} minutes of trying"
        )

    @abstractmethod
    def predict_batch(self, inputs: List[Any]) -> List[Any]:
        raise NotImplementedError

    def predict_single(self, single: Any) -> Any:
        """
        input: Any input
        """
        return self.predict_batch([single])[0]
