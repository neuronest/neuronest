from functools import lru_cache
from typing import Optional

from google.cloud import resourcemanager_v3

from core.client.abstract.base_client import BaseClient


class ProjectManager(BaseClient):
    def __init__(self, project_id: str, key_path: Optional[str] = None):
        super().__init__(key_path=key_path, project_id=project_id)
        self.projects_client = resourcemanager_v3.ProjectsClient(
            credentials=self.credentials
        )

    @lru_cache
    def get_project_number(self) -> str:
        project = self.projects_client.get_project(name=f"projects/{self.project_id}")

        return project.name.split("/")[-1]
