from core.routes.model_instantiator import route
from fastapi import APIRouter

from model_instantiator.api.instantiate import router as instantiate_router
from model_instantiator.api.uninstantiate import router as uninstantiate_router

router = APIRouter(prefix=route.root)

router.include_router(instantiate_router)
router.include_router(uninstantiate_router)


@router.get("/healthcheck")
def healthcheck():
    return {"status": "OK"}
