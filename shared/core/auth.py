from typing import Optional, Union

from google.auth import default
from google.auth.impersonated_credentials import Credentials as ImpersonatedCredentials
from google.auth.impersonated_credentials import (
    IDTokenCredentials as ImpersonatedIDTokenCredentials,
)
from google.auth.transport.requests import Request
from google.oauth2 import id_token
from google.oauth2.service_account import Credentials, IDTokenCredentials


def _generate_identity_token_credentials(
    target_audience: Optional[str],
    key_path: Optional[str] = None,
    credentials: Optional[Credentials] = None,
) -> Union[IDTokenCredentials, ImpersonatedIDTokenCredentials]:
    """
    Creates IDTokenCredentials for the specified target audience.

    Args:
        target_audience (str): The audience for which the ID token is generated.
        key_path (Optional[str]): Path to a service account key file.
            Ignored if `credentials` is provided.
        credentials (Optional[Credentials]): An existing credentials object.
            Used if provided, instead of `key_path`.

    Returns:
        IDTokenCredentials: Credentials object for generating ID tokens.
    """
    if credentials and isinstance(credentials, ImpersonatedCredentials):
        return ImpersonatedIDTokenCredentials(
            target_credentials=credentials,
            target_audience="https://dummy.example.com"
            if target_audience is None
            else target_audience,
        )

    if key_path:
        # Create IDTokenCredentials from the provided key file
        return IDTokenCredentials.from_service_account_file(
            key_path, target_audience=target_audience
        )

    # Fetch IDTokenCredentials from the current environment
    return id_token.fetch_id_token_credentials(audience=target_audience)


def generate_identity_token(
    target_audience: Optional[str] = None,
    key_path: Optional[str] = None,
    credentials: Optional[Credentials] = None,
) -> str:
    return _generate_token_from_credentials(
        _generate_identity_token_credentials(
            target_audience=target_audience,
            key_path=key_path,
            credentials=credentials,
        )
    )


def _generate_token_from_credentials(
    credentials: Union[Credentials, IDTokenCredentials]
) -> str:
    credentials.refresh(Request())

    if credentials.valid is False:
        raise ValueError("Could not get valid token")

    return credentials.token


def get_credentials(
    key_path: Optional[str] = None,
    auth_scope: str = "https://www.googleapis.com/auth/cloud-platform",
) -> Credentials:
    if key_path is not None:
        return Credentials.from_service_account_file(key_path, scopes=[auth_scope])

    credentials, _ = default(scopes=[auth_scope])

    return credentials


def generate_access_token(key_path: str) -> str:
    return _generate_token_from_credentials(
        credentials=get_credentials(key_path=key_path)
    )
