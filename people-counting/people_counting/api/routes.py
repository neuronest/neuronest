from core.routes.people_counting import routes
from fastapi import APIRouter

from people_counting.api.people_counter import router as people_counter_router
from people_counting.api.resources import router as resources_router

router = APIRouter(prefix=routes.root)

router.include_router(people_counter_router)
router.include_router(resources_router)


@router.get("/healthcheck")
def healthcheck():
    return {"status": "OK"}
