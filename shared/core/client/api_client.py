from __future__ import annotations

import abc
import json
import logging
from enum import Enum
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import requests

from core.auth import generate_identity_token
from core.client.base_client import BaseClient


class Protocol(str, Enum):
    HTTP = "http"
    HTTPS = "https"

    @classmethod
    def from_ssl(cls, ssl: bool) -> Protocol:
        if ssl is True:
            return cls.HTTPS

        return cls.HTTP


class APIClient(BaseClient, abc.ABC):
    def __init__(
        self,
        host: str,
        root: str,
        key_path: Optional[str],
        ssl: bool = True,
        project_id: Optional[str] = None,
    ):
        super().__init__(key_path=key_path, project_id=project_id)
        self.host = host
        self.root = root
        self.protocol_with_host = self._build_host_with_protocol(host=host, ssl=ssl)
        self.endpoint = f"{self.protocol_with_host}{root}"

    @staticmethod
    def _build_host_with_protocol(host: str, ssl: bool) -> str:
        constructed_protocol = Protocol.from_ssl(ssl=ssl)
        # Check if the host already contains a protocol
        # If it does, we detect it and avoid rebuilding it
        # This is important to prevent conflicts with the ssl flag (True or False)
        if any(
            host.startswith(f"{protocol}://")
            for protocol in [Protocol.HTTP, Protocol.HTTPS]
        ):
            if not host.startswith(constructed_protocol):
                logging.warning(
                    f"A host with protocol {constructed_protocol} was requested, "
                    f"but the host {host} has a conflicting protocol already present"
                )
            return host

        parsed_host = urlparse(host)

        if parsed_host.scheme == "":
            return f"{constructed_protocol}://{host}"

        if parsed_host.scheme != constructed_protocol:
            raise ValueError(
                f"Expected protocol to be '{constructed_protocol}' from ssl={ssl}, "
                f"could not deduce it from host: {host}"
            )

        return host

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
