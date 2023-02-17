from threading import Thread
from typing import Optional

import requests

from core.client.base import APIClient
from core.schemas.model_instantiator import (
    InstantiateModelInput,
    UninstantiateModelInput,
)


class ModelInstantiatorClient(APIClient):
    def __init__(
        self, key_path: str, host: str, wait_for_server_response: bool = False
    ):
        super().__init__(key_path=key_path, host=host)
        self.wait_for_server_response = wait_for_server_response

    def instantiate(self, model_name: str) -> Optional[requests.Response]:
        instantiate_call_parameters = dict(
            resource="instantiate",
            verb="post",
            payload=InstantiateModelInput(model_name=model_name).dict(),
        )

        if self.wait_for_server_response is True:
            return self.call(**instantiate_call_parameters)

        Thread(target=self.call, kwargs=instantiate_call_parameters).start()

        return None

    def uninstantiate(self, model_name: str) -> requests.Response:
        return self.call(
            resource="uninstantiate",
            verb="post",
            payload=UninstantiateModelInput(model_name=model_name).dict(),
        )
