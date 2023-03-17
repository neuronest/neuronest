from core.routes.people_counting import route
from fastapi import APIRouter

from people_counting.api.people_counter import router as people_counter_router

router = APIRouter(prefix=route.root)

router.include_router(people_counter_router)


@router.get("/healthcheck")
def healthcheck():
    return {"status": "OK"}
