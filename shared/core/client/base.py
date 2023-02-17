import abc
import json
from typing import Any, Dict, Optional

import requests

from core.auth import generate_identity_token


class APIClient(abc.ABC):
    def __init__(
        self, key_path: str, host: str, ssl: bool = True, prefix: str = "api/v1"
    ):
        self.key_path = key_path
        protocol = "https" if ssl is True else "http"
        self.protocol_with_host = f"{protocol}://{host}"
        self.endpoint = f"{self.protocol_with_host}/{prefix}"

    def auth_headers(self) -> Dict[str, str]:
        identity_token = generate_identity_token(
            key_path=self.key_path, target_audience=self.protocol_with_host
        )

        return {"Authorization": f"Bearer {identity_token}"}

    # noinspection PyMethodMayBeStatic
    def auth_params(self) -> Dict[str, str]:
        return {}

    def _request(
        self,
        resource: str,
        method: str,
        payload: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        content_type_value: str = "application/json; charset=utf-8",
    ) -> requests.Request:
        content_type = {"Content-Type": content_type_value}

        return requests.Request(
            method=method,
            url=f"{self.endpoint}/{resource}",
            headers={**content_type, **self.auth_headers()},
            params={**self.auth_params(), **(params or {})},
            data=json.dumps(payload or {}),
        )

    def call(
        self,
        resource: str,
        verb: str,
        payload: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> requests.Response:
        request = self._request(resource, verb, payload, params).prepare()
        session = requests.Session()
        response = session.send(request)
        response.raise_for_status()

        return response
