def get_service_account_email(service_account_name: str, project_id: str):
    return f"{service_account_name}@{project_id}.iam.gserviceaccount.com"
