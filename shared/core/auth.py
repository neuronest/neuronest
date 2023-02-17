from typing import Union

from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials, IDTokenCredentials


def _get_id_token_credentials(
    key_path: str, target_audience: str
) -> IDTokenCredentials:
    return IDTokenCredentials.from_service_account_file(
        key_path, target_audience=target_audience
    )


def _get_credentials(
    key_path: str, auth_scope: str = "https://www.googleapis.com/auth/cloud-platform"
) -> Credentials:
    return Credentials.from_service_account_file(key_path, scopes=[auth_scope])


def _generate_token_from_credentials(
    credentials: Union[Credentials, IDTokenCredentials]
) -> str:
    credentials.refresh(Request())

    if credentials.valid is False:
        raise ValueError("Could not get valid token")

    return credentials.token


def generate_identity_token(key_path: str, target_audience: str) -> str:
    return _generate_token_from_credentials(
        credentials=_get_id_token_credentials(
            key_path=key_path, target_audience=target_audience
        )
    )


def generate_access_token(key_path: str) -> str:
    return _generate_token_from_credentials(
        credentials=_get_credentials(key_path=key_path)
    )
