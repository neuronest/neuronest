from typing import Optional, Union

from google.auth import default
from google.auth.transport.requests import Request
from google.oauth2 import id_token
from google.oauth2.service_account import Credentials, IDTokenCredentials


def _get_id_token_credentials(
    target_audience: str,
    key_path: Optional[str] = None,
) -> IDTokenCredentials:
    if key_path is not None:
        return IDTokenCredentials.from_service_account_file(
            key_path, target_audience=target_audience
        )

    # create IDTokenCredentials from current environment
    return id_token.fetch_id_token_credentials(audience=target_audience)


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


def generate_identity_token(
    target_audience: Optional[str] = None,
    key_path: Optional[str] = None,
    credentials: Optional[Credentials] = None,
) -> str:
    """
    Generates an identity token for the specified target audience.

    Args:
        target_audience (str): The audience for which the ID token is generated.
        key_path (Optional[str]): Path to a service account key file.
            Ignored if `credentials` is provided.
        credentials (Optional[Credentials]): Directly provided credentials.
            If `None`, falls back to `key_path`.

    Returns:
        str: A generated identity token.
    """
    if not credentials and not key_path:
        raise ValueError("Either `credentials` or `key_path` must be provided.")

    if not credentials:
        # Load credentials from the service account key file
        credentials = _get_id_token_credentials(
            target_audience=target_audience, key_path=key_path
        )

    return _generate_token_from_credentials(credentials=credentials)


def generate_access_token(key_path: str) -> str:
    return _generate_token_from_credentials(
        credentials=get_credentials(key_path=key_path)
    )
