from typing import List

from core.routes.database_api import routes
from core.schemas.database_api import Project, ProjectCreate
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from database_api.api.dependencies import get_database
from database_api.models.project import Project as DatabaseProject

router = APIRouter(prefix=f"/{routes.Project.prefix}", tags=[routes.Project.prefix])


def _deleted_project_response(response: Response, gcp_project_id: str) -> Response:
    """
    Constructs a response message for a successfully deleted project
    and sets the response status code and body.

    The body is encoded to UTF-8 because HTTP response bodies must be
    bytes objects, not strings. Encoding the string ensures compatibility
    with the HTTP protocol and avoids runtime errors in ASGI frameworks.
    """
    response.status_code = status.HTTP_200_OK
    response.body = (
        f"Project with gcp_project_id {gcp_project_id} has been deleted".encode("utf-8")
    )

    return response


@router.post(routes.Project.create, response_model=Project)
def create(project: ProjectCreate, database: Session = Depends(get_database)):
    db_project = (
        database.query(DatabaseProject)
        .filter(DatabaseProject.gcp_project_id == project.gcp_project_id)
        .first()
    )
    if db_project:
        raise HTTPException(status_code=400, detail="Project already exists")

    new_db_project = DatabaseProject(gcp_project_id=project.gcp_project_id)
    database.add(new_db_project)
    database.commit()
    database.refresh(new_db_project)

    return new_db_project


@router.get(routes.Project.get, response_model=Project)
def get(gcp_project_id: str, database: Session = Depends(get_database)):
    """
    Retrieve a project by its GCP project ID.
    """
    db_project = (
        database.query(DatabaseProject)
        .filter(DatabaseProject.gcp_project_id == gcp_project_id)
        .first()
    )
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")

    return db_project


@router.get(routes.Project.list, response_model=List[Project])
# pylint: disable=redefined-builtin
def list(database: Session = Depends(get_database)):
    return database.query(DatabaseProject).all()


@router.delete(routes.Project.delete)
def delete(
    gcp_project_id: str, response: Response, database: Session = Depends(get_database)
):
    """
    Delete a project by its GCP project ID.
    """
    db_project = (
        database.query(DatabaseProject)
        .filter(DatabaseProject.gcp_project_id == gcp_project_id)
        .first()
    )
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")

    database.delete(db_project)
    database.commit()

    # Use the helper function to construct the response
    return _deleted_project_response(response=response, gcp_project_id=gcp_project_id)
