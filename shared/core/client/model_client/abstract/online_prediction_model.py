import random
import time
from abc import ABC
from typing import List, Optional, Type

import requests
from google.api_core.exceptions import ServiceUnavailable
from google.cloud import aiplatform

from core.client.abstract.base_client import BaseClient
from core.client.model_instantiator import ModelInstantiatorClient
from core.exceptions import DependencyError
from core.google.vertex_ai_manager import VertexAIManager
from core.schemas.abstract.online_prediction_model import (
    InputSampleSchema,
    OutputSampleSchema,
)
from core.tools import flatten_iterables, split_list_into_two_parts


class OnlinePredictionModelClient(BaseClient, ABC):
    INPUT_SAMPLE_SCHEMA: Type[InputSampleSchema]
    OUTPUT_SAMPLE_SCHEMA: Type[OutputSampleSchema]
    MAX_BYTES = 1e8

    # pylint: disable=too-many-positional-arguments
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

        if self.INPUT_SAMPLE_SCHEMA is None:
            raise RuntimeError("Input schema must be specified")

        if self.OUTPUT_SAMPLE_SCHEMA is None:
            raise RuntimeError("Output schema must be specified")

    def _create_endpoint(self) -> Optional[requests.Response]:
        return self.model_instantiator_client.instantiate(self.model_name)

    def _try_get_or_create_latest_model_endpoint(self) -> aiplatform.Endpoint:
        total_waited_time = 0

        while total_waited_time < self.endpoint_retry_timeout:
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

    def _calculate_endpoint_input_bytes_length(
        self, samples: List[InputSampleSchema]
    ) -> int:
        return self.vertex_ai_manager.calculate_prediction_payload_size(
            instances=[sample.serialize() for sample in samples]
        )

    def _split_into_chunks(
        self, samples: List[InputSampleSchema]
    ) -> List[List[InputSampleSchema]]:
        if len(samples) == 0:
            return [[]]

        if len(samples) == 1:
            return [samples]

        if (
            self._calculate_endpoint_input_bytes_length(samples=samples)
            <= self.MAX_BYTES
        ):
            return [samples]

        for index, sample in enumerate(samples):
            if (
                endpoint_input_bytes_length := (
                    self._calculate_endpoint_input_bytes_length(samples=[sample])
                )
            ) > self.MAX_BYTES:
                raise ValueError(
                    f"Cannot proceed input_sample_schema at index {index} is too "
                    f"large: {endpoint_input_bytes_length / 1e6}MB"
                )

        current_chunks = [samples[0]]
        current_chunk_bytes_length = self._calculate_endpoint_input_bytes_length(
            samples=current_chunks
        )

        for sample in samples[1:]:
            sample_bytes_length = self._calculate_endpoint_input_bytes_length(
                samples=[sample]
            )

            if current_chunk_bytes_length + sample_bytes_length <= self.MAX_BYTES:
                current_chunks[-1].append(sample)
                current_chunk_bytes_length += sample_bytes_length
                continue

            current_chunks.append([sample])
            current_chunk_bytes_length = sample_bytes_length

        return current_chunks

    # pylint: disable=too-many-positional-arguments
    def _predict_batch(
        self,
        samples: List[InputSampleSchema],
        max_tries: int = 5,
        base_retry_delay: float = 1.0,
        max_retry_delay: float = 32.0,
        current_try: int = 0,
        # absurdly long, we do not want to handle custom value for each model
        timeout: Optional[float] = 3600,
    ) -> List[OutputSampleSchema]:
        if len(samples) == 0:
            return []

        # todo: trouver un moyen de remove les interactions reseau type get endpoint
        # pendant online prediction où le but c'est la latence minimum
        endpoint = self._try_get_or_create_latest_model_endpoint()
        from datetime import datetime
        if (datetime.now(endpoint.update_time.tzinfo) - endpoint.update_time).total_seconds() < 5*60:
            time.sleep(5*60)


        try:
            # todo: un peu bancal pour le futur, on est sur une fonction sans limite de
            # nombre de samples mais avec les mêmes default values max_tries etc
            # pour tous les scénarios
            # la logique ServiceUnavailable devrait opérer au niveau du sample, pas du
            # batch, pour représenter une charge de travail bornée pour laquelle
            # les default values ont du sens
            return [
                self.OUTPUT_SAMPLE_SCHEMA.deserialize(prediction)
                for prediction in endpoint.predict(
                    [sample.serialize() for sample in samples], timeout=timeout
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
            left_samples_chunk, right_samples_chunk = split_list_into_two_parts(samples)

            return self._predict_batch(
                samples=left_samples_chunk,
                max_tries=max_tries,
                current_try=current_try,
            ) + self._predict_batch(
                samples=right_samples_chunk,
                max_tries=max_tries,
                current_try=current_try,
            )

    def _verify_input_types(self, samples: List[InputSampleSchema]):
        if any(not isinstance(sample, self.INPUT_SAMPLE_SCHEMA) for sample in samples):
            raise ValueError(f"Expected {self.INPUT_SAMPLE_SCHEMA} input type")

    def predict_batch(
        self,
        samples: List[InputSampleSchema],
    ) -> List[OutputSampleSchema]:
        self._verify_input_types(samples=samples)

        chunks_samples = self._split_into_chunks(samples)

        return list(
            flatten_iterables(
                self._predict_batch(chunk_samples) for chunk_samples in chunks_samples
            )
        )

    def predict_single(
        self,
        sample: InputSampleSchema,
    ) -> OutputSampleSchema:
        return self.predict_batch(
            [sample],
        )[0]
