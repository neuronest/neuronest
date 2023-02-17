import time
from typing import List, Optional

import numpy as np
import pandas as pd
import requests
from cachetools.func import ttl_cache
from google.cloud import aiplatform

from core.client.model_instantiator import ModelInstantiatorClient
from core.exceptions import DependencyError
from core.google.vertex_ai_manager import VertexAIManager
from core.schemas.object_detection import PREDICTION_COLUMNS, OutputSchema
from core.serialization.array import array_from_string
from core.serialization.image import image_to_string


class ObjectDetectionClient:
    def __init__(
        self,
        vertex_ai_manager: VertexAIManager,
        model_instantiator_client: ModelInstantiatorClient,
        model_name: str,
        endpoint_retry_wait_time: int = 30,
        endpoint_retry_timeout: int = 1800,
    ):
        self.vertex_ai_manager = vertex_ai_manager
        self.model_instantiator_client = model_instantiator_client
        self.model_name = model_name
        self.endpoint_retry_wait_time = endpoint_retry_wait_time
        self.endpoint_retry_timeout = endpoint_retry_timeout

    def _create_endpoint(self) -> Optional[requests.Response]:
        return self.model_instantiator_client.instantiate(self.model_name)

    @ttl_cache(ttl=600)
    def _try_get_endpoint(self, attempt_iteration: int = 0) -> aiplatform.Endpoint:
        endpoint = self.vertex_ai_manager.get_endpoint_by_name(self.model_name)

        if endpoint is not None:
            return endpoint

        if (
            attempt_iteration
            > self.endpoint_retry_timeout // self.endpoint_retry_wait_time
        ):
            raise DependencyError(
                f"Failed to deploy an endpoint for model_name={self.model_name}, "
                f"giving up after {self.endpoint_retry_timeout // 60} minutes of trying"
            )

        self._create_endpoint()
        time.sleep(self.endpoint_retry_wait_time)

        return self._try_get_endpoint(attempt_iteration=attempt_iteration + 1)

    def predict_batch(self, images: List[np.ndarray]) -> List[pd.DataFrame]:
        endpoint = self._try_get_endpoint()

        raw_predictions = endpoint.predict(
            [{"data": image_to_string(image)} for image in images]
        ).predictions
        predictions = [
            array_from_string(OutputSchema.parse_obj(raw_prediction).results)
            for raw_prediction in raw_predictions
        ]

        return [
            pd.DataFrame(prediction, columns=PREDICTION_COLUMNS)
            for prediction in predictions
        ]

    def predict_single(self, image: np.ndarray) -> pd.DataFrame:
        return self.predict_batch([image])[0]
