import json
import os
from abc import ABC
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import backoff
import requests
from requests import HTTPError

from core.auth import generate_identity_token
from core.client.abstract.base_client import BaseClient
from core.schemas.protocol import Protocol


class APIClient(BaseClient, ABC):
    # pylint: disable=too-many-positional-arguments
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

    # pylint: disable=too-many-positional-arguments
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

    @staticmethod
    def _check_response(
        response: requests.Response, verbose_on_exception: bool
    ) -> None:
        """
        Raise HTTPError with additional information if the response is not successful.
        """
        try:
            response.raise_for_status()
        except HTTPError as http_error:
            if verbose_on_exception:
                error_message = os.linesep.join(
                    [
                        str(http_error),
                        f"response text: {http_error.response.text}",
                        f"request payload: {http_error.response.request.body}",
                    ]
                )
                raise HTTPError(
                    error_message, response=http_error.response
                ) from http_error
            raise http_error

    def _send_request(
        self,
        prepared_request: requests.PreparedRequest,
        timeout: Optional[int],
        verbose_on_exception: bool,
    ) -> requests.Response:
        """Send the prepared request and return the response after error checking."""
        session = requests.Session()
        response = session.send(prepared_request, timeout=timeout)
        self._check_response(response, verbose_on_exception)
        return response

    # pylint: disable=too-many-positional-arguments
    def call(
        self,
        resource: str,
        verb: str,
        payload: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
        target_audience: str = None,
        http_retry_attempts: Optional[int] = 0,
        connection_retry_attempts: Optional[int] = 1,
        verbose_on_exception: bool = True,
    ) -> requests.Response:
        request = self._request(
            resource, verb, payload, params, target_audience=target_audience
        ).prepare()

        # Wrap the send action with backoff if needed.
        _call = self._send_request

        if http_retry_attempts != 0:
            # backoff.on_exception is used. Rule is that if max_tries is None then
            # unlimited number of retries
            _call = backoff.on_exception(
                backoff.expo,
                (requests.exceptions.HTTPError, requests.exceptions.ConnectionError),
                max_tries=http_retry_attempts,
            )(self._send_request)

        if connection_retry_attempts != 0:
            _call = backoff.on_exception(
                backoff.expo,
                (requests.exceptions.HTTPError, requests.exceptions.ConnectionError),
                max_tries=connection_retry_attempts,
            )(self._send_request)

        return _call(request, timeout, verbose_on_exception)
