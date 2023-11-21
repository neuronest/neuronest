from abc import ABC, abstractmethod
from typing import Dict, Type

from core.client.factory import ServiceClient, ServiceClientFactory
from core.schemas.service_evaluator import EvaluatedServiceName

from service_evaluator.dataset_manager import DatasetManager


class PredictorMixin(ABC):
    def __init__(
        self,
        service_client_parameters: Dict[str, str],
        service_name: EvaluatedServiceName,
        expected_client_class: Type[ServiceClient],
    ):
        self.client: ServiceClient = ServiceClientFactory.new(
            service_name=service_name, **service_client_parameters
        )

        if not isinstance(self.client, expected_client_class):
            raise RuntimeError(
                f"Expected instantiated client to be an instance of "
                f"{expected_client_class}, got {type(self.client)}"
            )

    @abstractmethod
    def run(self, dataset_manager: DatasetManager):
        raise NotImplementedError
