from typing import List

from core.routes.database_api import routes
from core.schemas.database_api import Project, ProjectCreate
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from database_api.api.dependencies import get_database
from database_api.models.project import Project as DatabaseProject

router = APIRouter(prefix=f"/{routes.Project.prefix}", tags=[routes.Project.prefix])


def _modify_response_status_return_message(
    response: Response, message: str, status_code: int
):
    response.status_code = status_code

    return {"message": message}


def _project_already_exists_response(
    response: Response,
    project_id: str,
    status_code: int = status.HTTP_409_CONFLICT,
):
    return _modify_response_status_return_message(
        response=response,
        message=f"Project {project_id} already exists",
        status_code=status_code,
    )


@router.post(routes.Project.create, response_model=Project)
def create(
    project: ProjectCreate,
    response: Response,
    database: Session = Depends(get_database),
):
    db_project = (
        database.query(DatabaseProject)
        .filter(DatabaseProject.gcp_project_id == project.gcp_project_id)
        .first()
    )
    if db_project:
        return _project_already_exists_response(
            response=response, project_id=project.gcp_project_id
        )

    new_db_project = DatabaseProject(gcp_project_id=project.gcp_project_id)
    database.add(new_db_project)
    database.commit()
    database.refresh(new_db_project)

    return new_db_project


@router.delete(routes.Project.delete)
def delete(gcp_project_id: str, database: Session = Depends(get_database)):
    """
    Delete a project by its GCP project ID.
    """
    db_project = (
        database.query(DatabaseProject)
        .filter(DatabaseProject.gcp_project_id == gcp_project_id)
        .first()
    )
    if not db_project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    database.delete(db_project)
    database.commit()


@router.get(routes.Project.list, response_model=List[Project])
# pylint: disable=redefined-builtin
def list(database: Session = Depends(get_database)):
    return database.query(DatabaseProject).all()
