from pydantic import BaseModel


class ProjectCreate(BaseModel):
    gcp_project_id: str

    class Config:
        orm_mode = True


class Project(ProjectCreate):
    pass
