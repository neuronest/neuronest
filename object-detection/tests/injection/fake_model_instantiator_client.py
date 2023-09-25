from typing import Optional

import requests
from core.client.model_instantiator import ModelInstantiatorClient


class FakeModelInstantiatorClient(ModelInstantiatorClient):
    def instantiate(self, model_name: str) -> Optional[requests.Response]:
        response = requests.Response()
        response.status_code = "201"

        return response

    def uninstantiate(self, model_name: str) -> requests.Response:
        response = requests.Response()
        response.status_code = "202"

        return response
