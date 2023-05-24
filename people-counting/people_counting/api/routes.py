from fastapi import APIRouter

from people_counting.api.people_counter import router as people_counter_router

router = APIRouter(prefix="/v1")

router.include_router(people_counter_router)


@router.get("/healthcheck")
def healthcheck():
    return {"status": "OK"}
