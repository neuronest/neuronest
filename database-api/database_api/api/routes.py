from core.routes.database_api import routes
from fastapi import APIRouter

from database_api.api.project import router as project_router

router = APIRouter(prefix=routes.root)

router.include_router(project_router)


@router.get("/healthcheck")
def healthcheck():
    return {"status": "OK"}
