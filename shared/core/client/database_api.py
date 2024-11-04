from typing import Optional

import requests

from core.client.api_client import APIClient
from core.routes.database_api import routes
from core.schemas.database_api import RoutesSchemas


class DatabaseApiClient(APIClient):
    def __init__(self, host: str, key_path: Optional[str] = None):
        super().__init__(host=host, key_path=key_path, root=routes.root)

    # first  action description then model name
    def create_project(self, gcp_project_id: str) -> requests.Response:
        return self.call(
            resource=f"/{routes.Project.prefix}" f"{routes.Project.create}",
            verb="post",
            payload=RoutesSchemas.ProjectCreate(gcp_project_id=gcp_project_id).dict(),
        )
