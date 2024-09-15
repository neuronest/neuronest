from core.routes.video_comparator import routes
from fastapi import APIRouter

from video_comparator.api.resources import router as resources_router
from video_comparator.api.video_comparator import router as video_comparator_router

router = APIRouter(prefix=routes.root)

router.include_router(video_comparator_router)
router.include_router(resources_router)


@router.get("/healthcheck")
def healthcheck():
    return {"status": "OK"}
