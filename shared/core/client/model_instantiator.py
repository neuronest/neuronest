import requests

from core.client.api_client import APIClient
from core.routes.model_instantiator import route
from core.schemas.model_instantiator import (
    InstantiateModelInput,
    UninstantiateModelInput,
)


class ModelInstantiatorClient(APIClient):
    def __init__(self, key_path: str, host: str):
        super().__init__(key_path=key_path, host=host, root=route.root)

    def instantiate(self, model_name: str) -> requests.Response:
        instantiate_call_parameters = {
            "resource": route.instantiate,
            "verb": "post",
            "payload": InstantiateModelInput(model_name=model_name).dict(),
        }

        return self.call(**instantiate_call_parameters)

    def uninstantiate(self, model_name: str) -> requests.Response:
        return self.call(
            resource=route.uninstantiate,
            verb="post",
            payload=UninstantiateModelInput(model_name=model_name).dict(),
        )
