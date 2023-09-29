from __future__ import annotations

import json
from abc import ABC
from enum import Enum
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import requests

from core.auth import generate_identity_token, get_credentials


class Protocol(str, Enum):
    HTTP = "http"
    HTTPS = "https"

    @classmethod
    def from_ssl(cls, ssl: bool) -> Protocol:
        if ssl is True:
            return cls.HTTPS

        return cls.HTTP


class APIClient(ABC):
    def __init__(
        self,
        host: str,
        root: str,
        key_path: Optional[str] = None,
        ssl: Optional[bool] = None,
        project_id: Optional[str] = None,
    ):
        self.host = host
        self.root = root
        self.key_path = key_path
        self.protocol_with_host = self._build_host_with_protocol(host=host, ssl=ssl)
        self.endpoint = f"{self.protocol_with_host}{root}"
        self.credentials = get_credentials(key_path=self.key_path)
        self._project_id = project_id

    @property
    def project_id(self) -> str:
        # we give priority on the project_id which was passed explicitly to the
        # instantiation rather than to the project id to which the service account
        # of the credentials is attached
        return (
            self._project_id
            if self._project_id is not None
            else self.credentials.project_id
        )

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
