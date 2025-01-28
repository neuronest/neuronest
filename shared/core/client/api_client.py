from __future__ import annotations

import json
import os
from abc import ABC
from enum import Enum
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import backoff
import requests
from requests import HTTPError

from core.auth import generate_identity_token, get_credentials
from core.client.base_client import BaseClient


class Protocol(str, Enum):
    HTTP = "http"
    HTTPS = "https"

    @classmethod
    def from_ssl(cls, ssl: bool) -> Protocol:
        if ssl is True:
            return cls.HTTPS

        return cls.HTTP


class APIClient(BaseClient, ABC):
    def __init__(
        self,
        host: str,
        root: str,
        key_path: Optional[str],
        ssl: Optional[bool] = None,
        project_id: Optional[str] = None,
    ):
        super().__init__(key_path=key_path, project_id=project_id)
        self.host = host
        self.root = root
        self.key_path = key_path
        self.protocol_with_host = self._build_host_with_protocol(host=host, ssl=ssl)
        self.endpoint = f"{self.protocol_with_host}{root}"
        self.credentials = get_credentials(key_path=self.key_path)
        self._project_id = project_id

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

    def auth_headers(self, target_audience: str = None) -> Dict[str, str]:
        identity_token = generate_identity_token(
            target_audience=target_audience or self.host,
            key_path=self.key_path,
            credentials=self.credentials,
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
        target_audience: str = None,
    ) -> requests.Request:
        content_type = {"Content-Type": content_type_value}

        return requests.Request(
            method=method,
            url=f"{self.endpoint}{resource}",
            headers={
                **content_type,
                **self.auth_headers(target_audience=target_audience),
            },
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
        target_audience: str = None,
        retry_attempts: Optional[int] = 0,
        verbose_on_exception: bool = True,
    ) -> requests.Response:
        def _call():
            request = self._request(
                resource, verb, payload, params, target_audience=target_audience
            ).prepare()
            session = requests.Session()
            response = session.send(request, timeout=timeout)
            try:
                response.raise_for_status()
            except HTTPError as http_error:
                if verbose_on_exception:
                    raise HTTPError(
                        os.linesep.join(
                            [
                                str(http_error),
                                f"response text: {http_error.response.text}",
                                f"response text: {http_error.response.text}",
                                f"request payload: {http_error.response.request.body}",
                            ]
                        ),
                        response=http_error.response,
                    ) from http_error
                raise http_error
            return response

        if retry_attempts != 0:
            _call = backoff.on_exception(
                backoff.expo, HTTPError, max_tries=retry_attempts
            )(_call)

        return _call()
