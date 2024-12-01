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
