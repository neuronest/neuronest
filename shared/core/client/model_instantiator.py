from __future__ import annotations

from typing import Optional

import requests

from core.client.base import CloudRunBasedClient, HTTPClient
from core.routes.model_instantiator import routes
from core.schemas.model_instantiator import (
    InstantiateModelInput,
    UninstantiateModelInput,
)


class ModelInstantiatorClient(HTTPClient, CloudRunBasedClient):
    def __init__(self, host: str, key_path: Optional[str] = None):
        super().__init__(host=host, key_path=key_path, root=routes.root)

    @classmethod
    def from_primitive_attributes(cls, **kwargs) -> ModelInstantiatorClient:
        mandatory_fields = ("host",)
        optional_fields = ("key_path",)

        try:
            (host,) = [kwargs[mandatory_field] for mandatory_field in mandatory_fields]
        except KeyError as key_error:
            raise ValueError(
                f"At least one mandatory field is missing, expected fields: "
                f"{mandatory_fields}"
            ) from key_error

        optional_values = {
            optional_field: kwargs[optional_field]
            for optional_field in optional_fields
            if optional_field in kwargs
        }

        return cls(
            host=host,
            **optional_values,
        )

    def instantiate(self, model_name: str) -> requests.Response:
        return self.call(
            resource=f"/{routes.Instantiator.prefix}"
            f"{routes.Instantiator.instantiate}",
            verb="post",
            payload=InstantiateModelInput(model_name=model_name).dict(),
        )

    def uninstantiate(self, model_name: str) -> requests.Response:
        return self.call(
            resource=f"/{routes.Uninstantiator.prefix}"
            f"{routes.Uninstantiator.uninstantiate}",
            verb="post",
            payload=UninstantiateModelInput(model_name=model_name).dict(),
        )
