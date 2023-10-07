from typing import Optional

import requests

from core.client.base import APIClient
from core.routes.model_instantiator import routes
from core.schemas.model_instantiator import (
    InstantiateModelInput,
    UninstantiateModelInput,
)


class ModelInstantiatorClient(APIClient):
    def __init__(self, host: str, key_path: Optional[str] = None):
        super().__init__(host=host, key_path=key_path, root=routes.root)

    def instantiate(self, model_name: str) -> requests.Response:
        instantiate_call_parameters = {
            "resource": routes.Instantiator.instantiate,
            "verb": "post",
            "payload": InstantiateModelInput(model_name=model_name).dict(),
        }

        return self.call(**instantiate_call_parameters)

    def uninstantiate(self, model_name: str) -> requests.Response:
        return self.call(
            resource=routes.Uninstantiator.uninstantiate,
            verb="post",
            payload=UninstantiateModelInput(model_name=model_name).dict(),
        )
