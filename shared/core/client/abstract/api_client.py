import json
from abc import ABC
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import backoff
import requests

from core.auth import generate_identity_token, get_credentials
from core.client.abstract.base_client import BaseClient
from core.schemas.protocol import Protocol


class APIClient(BaseClient, ABC):
    def __init__(
        self,
        host: str,
        root: str,
        key_path: Optional[str],
        ssl: Optional[bool] = None,
        project_id: Optional[str] = None,
        http_call_max_retry_attempts: int = 5,
    ):
        super().__init__(key_path=key_path, project_id=project_id)
        self.host = host
        self.root = root
        self.key_path = key_path
        self.protocol_with_host = self._build_host_with_protocol(host=host, ssl=ssl)
        self.endpoint = f"{self.protocol_with_host}{root}"
        self.credentials = get_credentials(key_path=self.key_path)
        self._project_id = project_id
        self._http_call_max_retry_attempts = http_call_max_retry_attempts

    @staticmethod
    def _build_host_with_protocol(host: str, ssl: Optional[bool]) -> str:
        parsed_host = urlparse(host)

        if parsed_host.scheme == "":
            if ssl is None:
                raise ValueError(
                    "The parameter 'ssl' should be specified in the case where the "
                    "protocol is not contained in the host"
                )

            constructed_protocol = Protocol.from_ssl(ssl=ssl)
            return f"{constructed_protocol}://{host}"

        return host

    def auth_headers(self) -> Dict[str, str]:
        identity_token = generate_identity_token(
            target_audience=self.protocol_with_host, key_path=self.key_path
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
            url=f"{self.endpoint}{resource}",
            headers={**content_type, **self.auth_headers()},
            params={**self.auth_params(), **(params or {})},
            data=json.dumps(payload or {}) if payload else None,
        )

    def call(
        self,
        resource: str,
        verb: str,
        payload: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
    ) -> requests.Response:
        @backoff.on_exception(
            backoff.expo,
            (requests.exceptions.HTTPError, requests.exceptions.ConnectionError),
            max_tries=self._http_call_max_retry_attempts,
        )
        def _do_call() -> requests.Response:
            request = self._request(resource, verb, payload, params).prepare()
            session = requests.Session()
            response = session.send(request, timeout=timeout)
            response.raise_for_status()

            return response

        return _do_call()
