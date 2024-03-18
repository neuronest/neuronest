import random
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type

import requests
from cachetools.func import ttl_cache
from google.api_core.exceptions import ServiceUnavailable
from google.cloud import aiplatform

from core.client.base_client import BaseClient
from core.client.model_instantiator import ModelInstantiatorClient
from core.exceptions import DependencyError
from core.google.vertex_ai_manager import VertexAIManager
from core.schemas.abstract.online_prediction_model import (
    InputSampleSchema,
    OutputSampleSchema,
)
from core.serialization.schema import Schema
from core.tools import merge_chunks_get_elements, split_list_into_two_parts


class OnlinePredictionModelClient(BaseClient, ABC):
    MAX_BYTES = 1.5e6

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

    def _calculate_endpoint_input_samples_schema_bytes(
        self, input_samples_schema_chunk: List[InputSampleSchema]
    ) -> int:
        return self.vertex_ai_manager.calculate_prediction_payload_size(
            instances=[
                input_sample_schema.serialized_attributes_dict()
                for input_sample_schema in input_samples_schema_chunk
            ]
        )

    def _split_into_chunks(
        self, input_samples_schema: List[InputSampleSchema]
    ) -> List[List[InputSampleSchema]]:
        if len(input_samples_schema) == 0:
            return []

        if len(input_samples_schema) == 1:
            return [input_samples_schema]

        if (
            self._calculate_endpoint_input_samples_schema_bytes(
                input_samples_schema_chunk=input_samples_schema
            )
            <= self.MAX_BYTES
        ):
            # a list of lists must be returned
            return [input_samples_schema]

        for index, input_sample_schema in enumerate(input_samples_schema):
            if (
                input_sample_schema_size_in_bytes := (
                    self._calculate_endpoint_input_samples_schema_bytes(
                        input_samples_schema_chunk=[input_sample_schema]
                    )
                )
            ) > self.MAX_BYTES:
                raise ValueError(
                    f"Cannot proceed input_sample_schema "
                    f"at index {index} is too large: "
                    f"{input_sample_schema_size_in_bytes / 1e6}MB"
                )

        input_samples_schema_chunks, current_input_samples_schema_chunk_bytes = [
            [input_samples_schema[0]]
        ], self._calculate_endpoint_input_samples_schema_bytes(
            input_samples_schema_chunk=[input_samples_schema[0]]
        )

        for input_sample_schema in input_samples_schema[1:]:
            current_input_sample_schema_bytes = (
                self._calculate_endpoint_input_samples_schema_bytes(
                    input_samples_schema_chunk=[input_sample_schema]
                )
            )
            if (
                current_input_sample_schema_bytes
                + current_input_samples_schema_chunk_bytes
                <= self.MAX_BYTES
            ):
                input_samples_schema_chunks[-1].append(input_sample_schema)
                current_input_samples_schema_chunk_bytes += (
                    current_input_sample_schema_bytes
                )
                continue

            input_samples_schema_chunks.append([input_sample_schema])
            current_input_samples_schema_chunk_bytes = current_input_sample_schema_bytes

        return input_samples_schema_chunks

    @abstractmethod
    def get_output_sample_schema_class(self) -> Type[OutputSampleSchema]:
        raise NotImplementedError

    def _predict_batch(
        self,
        input_samples_schema: List[InputSampleSchema],
        max_tries: int = 5,
        base_retry_delay: float = 1.0,
        max_retry_delay: float = 32.0,
        current_try: int = 0,
    ) -> List[OutputSampleSchema]:
        if len(input_samples_schema) == 0:
            return []

        endpoint = self._try_get_endpoint()

        output_sample_schema_class = self.get_output_sample_schema_class()

        if not issubclass(output_sample_schema_class, Schema):
            raise TypeError(
                f"{output_sample_schema_class.__name__} is not a subclass of "
                f"{Schema.__name__}"
            )

        try:
            return [
                self.get_output_sample_schema_class().from_serialized_attributes_dict(
                    prediction
                )
                for prediction in endpoint.predict(
                    [
                        input_sample_schema.serialized_attributes_dict()
                        for input_sample_schema in input_samples_schema
                    ]
                ).predictions
            ]
        except ServiceUnavailable as service_unavailable:
            current_try += 1
            if current_try > max_tries:
                raise service_unavailable

            # exponential backoff with random
            delay = min(base_retry_delay * (2**current_try), max_retry_delay)
            delay_with_random = random.uniform(base_retry_delay, delay)

            time.sleep(delay_with_random)

            # we divide the initial list into smaller chunks in case the size of the
            # initial list was an issue to be handled properly by the endpoint
            (
                left_input_samples_schema_chunk,
                right_input_samples_schema_chunk,
            ) = split_list_into_two_parts(input_samples_schema)

            return self._predict_batch(
                input_samples_schema=left_input_samples_schema_chunk,
                max_tries=max_tries,
                current_try=current_try,
            ) + self._predict_batch(
                input_samples_schema=right_input_samples_schema_chunk,
                max_tries=max_tries,
                current_try=current_try,
            )

    @abstractmethod
    def _batch_sample_to_input_sample_schema(
        self, batch_sample: Any, **input_sample_schema_kwargs: Optional[Dict[str, Any]]
    ) -> InputSampleSchema:
        raise NotImplementedError

    def _preprocess_batch(
        self, batch: List[Any], **input_sample_schema_kwargs: Optional[Dict[str, Any]]
    ) -> List[InputSampleSchema]:

        return [
            self._batch_sample_to_input_sample_schema(
                sample, **input_sample_schema_kwargs
            )
            for sample in batch
        ]

    # pylint: disable=arguments-renamed
    def predict_batch(
        self,
        batch: List[Any],
        **input_sample_schema_kwargs,
    ) -> List[OutputSampleSchema]:
        input_samples_schema = self._preprocess_batch(
            batch, **input_sample_schema_kwargs
        )

        input_samples_schema_chunks = self._split_into_chunks(input_samples_schema)

        return [
            merge_chunks_get_elements(
                self._predict_batch(input_samples_schema_chunk)
                for input_samples_schema_chunk in input_samples_schema_chunks
            )
        ]

    def predict_single(
        self,
        single: Any,
        **input_sample_schema_kwargs,
    ) -> Any:
        """
        input: Any input
        """
        return self.predict_batch(
            [single],
            **input_sample_schema_kwargs,
        )[0]
