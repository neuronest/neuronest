from core.routes.object_detection import routes
from fastapi import APIRouter

from object_detection.app.object_detection import router as object_detection_router
from object_detection.app.resources import router as resources_router

router = APIRouter(prefix=routes.root)

router.include_router(object_detection_router)
router.include_router(resources_router)


@router.get("/healthcheck")
def healthcheck():
    return {"status": "OK"}
