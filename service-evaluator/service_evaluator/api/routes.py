from core.routes.service_evaluator import routes
from fastapi import APIRouter

from service_evaluator.api.evaluate import router as evaluate_router

router = APIRouter(prefix=routes.root)

router.include_router(evaluate_router)


@router.get("/healthcheck")
def healthcheck():
    return {"status": "OK"}
