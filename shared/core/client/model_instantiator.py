import requests

from core.client.base import APIClient
from core.schemas.model_instantiator import (
    InstantiateModelInput,
    UninstantiateModelInput,
)


class ModelInstantiatorClient(APIClient):
    def __init__(self, key_path: str, host: str):
        super().__init__(key_path=key_path, host=host)

    def instantiate(self, model_name: str) -> requests.Response:
        instantiate_call_parameters = {
            "resource": "instantiate",
            "verb": "post",
            "payload": InstantiateModelInput(model_name=model_name).dict(),
        }

        return self.call(**instantiate_call_parameters)

    def uninstantiate(self, model_name: str) -> requests.Response:
        return self.call(
            resource="uninstantiate",
            verb="post",
            payload=UninstantiateModelInput(model_name=model_name).dict(),
        )
