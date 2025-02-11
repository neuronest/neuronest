from typing import Optional

import requests

from core.client.api_client import APIClient
from core.routes.database_api import routes
from core.schemas.database_api import ProjectCreate


class DatabaseApiClient(APIClient):
    def __init__(self, host: str, key_path: Optional[str] = None):
        super().__init__(host=host, key_path=key_path, root=routes.root)

    # first  action description then model name
    def create_project(self, gcp_project_id: str) -> requests.Response:
        return self.call(
            resource=f"/{routes.Project.prefix}{routes.Project.create}",
            verb="post",
            payload=ProjectCreate(gcp_project_id=gcp_project_id).dict(),
        )

    def get_project(self, gcp_project_id: str) -> requests.Response:
        """
        Fetch details of a project by its GCP project ID.
        """
        return self.call(
            resource=f"/{routes.Project.prefix}"
            f"{routes.Project.get.format(gcp_project_id=gcp_project_id)}",
            verb="get",
        )

    def list_projects(self) -> requests.Response:
        """
        Fetch details of a project by its GCP project ID.
        """
        return self.call(
            resource=f"/{routes.Project.prefix}" f"{routes.Project.list}",
            verb="get",
        )

    def delete_project(self, gcp_project_id: str) -> requests.Response:
        """
        Delete a project by its GCP project ID.
        """
        return self.call(
            resource=f"/{routes.Project.prefix}"
            f"{routes.Project.delete.format(gcp_project_id=gcp_project_id)}",
            verb="delete",
        )
