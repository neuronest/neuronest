import requests
from google.auth import default
from google.auth.exceptions import GoogleAuthError


def get_service_account_email(service_account_name: str, project_id: str):
    return f"{service_account_name}@{project_id}.iam.gserviceaccount.com"


def get_service_account_name_project_id_from_email(service_account_email: str):
    """
    Parse the service account email to retrieve the service account name and project ID.

    Args:
        service_account_email (str): The email of the service account in the format
            "{service_account_name}@{project_id}.iam.gserviceaccount.com".

    Returns:
        tuple: A tuple containing the service account name and the project ID.
    """
    # Split the email into parts using "@" and "."
    service_account_name, project_part = service_account_email.split("@")
    project_id = project_part.split(".")[0]

    return service_account_name, project_id


def fetch_active_service_account_email():
    """
    Fetches the currently active GCP Service Account email.

    :return: The active Service Account email as a string.
    :raises ValueError: If the credentials are retrieved but no service account email is found.
    :raises GoogleAuthError: If there is an issue retrieving credentials.
    :raises RuntimeError: For unexpected errors during the process.
    """
    metadata_url = (
        "http://metadata.google.internal/computeMetadata/v1"
        "/instance/service-accounts/default/email"
    )
    headers = {"Metadata-Flavor": "Google"}

    try:
        response = requests.get(metadata_url, headers=headers, timeout=2)
        if response.status_code == 200:
            return response.text
    except requests.RequestException:
        pass  # Ignore errors and fallback to default()
    try:
        credentials, _ = default()

        if (
            hasattr(credentials, "service_account_email")
            and credentials.service_account_email
        ):
            return credentials.service_account_email

        raise ValueError("Credentials retrieved, but no service account email found.")
    except GoogleAuthError as auth_error:
        raise GoogleAuthError(
            f"Failed to retrieve Service Account credentials: {auth_error}"
        ) from auth_error
    except Exception as error:
        raise RuntimeError(
            f"Unexpected error while retrieving Service Account: {error}"
        ) from error
