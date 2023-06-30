from core.routes.people_counting import people_counting_routes
from fastapi import APIRouter

from people_counting.api.people_counter import router as people_counter_router

router = APIRouter(prefix=people_counting_routes.root)

router.include_router(people_counter_router)


@router.get("/healthcheck")
def healthcheck():
    return {"status": "OK"}
