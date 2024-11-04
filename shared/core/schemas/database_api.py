from pydantic import BaseModel


class RoutesSchemas:
    class ProjectCreate(BaseModel):
        gcp_project_id: str
