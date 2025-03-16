from typing import List, Optional

import requests

from core.client.abstract.api_client import APIClient
from core.routes.database_api import routes
from core.schemas.modules.database_api import Project, ProjectCreate


class DatabaseApiClient(APIClient):
    def __init__(self, host: str, key_path: Optional[str] = None):
        super().__init__(host=host, key_path=key_path, root=routes.root)

    def create_project(self, gcp_project_id: str) -> Project:
        return Project(
            **self.call(
                resource=f"/{routes.Project.prefix}{routes.Project.create}",
                verb="post",
                payload=ProjectCreate(gcp_project_id=gcp_project_id).dict(),
            ).json()
        )

    def get_project(self, gcp_project_id: str) -> Project:
        return Project(
            **self.call(
                resource=f"/{routes.Project.prefix}"
                f"{routes.Project.get.format(gcp_project_id=gcp_project_id)}",
                verb="get",
            ).json()
        )

    def list_projects(self) -> List[Project]:
        return [
            Project(**project_data)
            for project_data in self.call(
                resource=f"/{routes.Project.prefix}{routes.Project.list}",
                verb="get",
            ).json()
        ]

    def delete_project(self, gcp_project_id: str) -> requests.Response:
        return self.call(
            resource=f"/{routes.Project.prefix}"
            f"{routes.Project.delete.format(gcp_project_id=gcp_project_id)}",
            verb="delete",
        )
