import json
import logging
import typing

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from starlette.requests import Request

import api.route.counter

logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)


def get_application() -> FastAPI:
    application = FastAPI()
    resources_router = APIRouter()
    resources_router.include_router(api.route.counter.router, prefix="/counter")
    application.include_router(resources_router)
    return application


app = get_application()


async def request_json_store_body(self) -> typing.Any:
    if not hasattr(self, "_json"):
        body = await self.body()
        self._json = json.loads(body)  # pylint: disable=protected-access
    self.scope["body"] = self._json  # pylint: disable=protected-access
    return self._json  # pylint: disable=protected-access


# override the method of the package to be able to access
# the body of the request a posteriori
Request.json = request_json_store_body


@app.exception_handler(HTTPException)
async def log_info_to_reproduce_http_exception(request, exc):
    logger.error(
        f"{exc} error for request method: {request.method} "
        f"url: {request.url} and body: {request.scope.get('body')}"
    )
    return await http_exception_handler(request, exc)


@app.exception_handler(Exception)
async def log_info_to_reproduce_exception(request, exc):
    logger.error(
        f"{exc} error for request method: {request.method} "
        f"url: {request.url} and body: {request.scope.get('body')}"
    )
    raise exc


@app.exception_handler(RequestValidationError)
async def log_info_to_reproduce_validation_exception(request, exc):
    logger.error(
        f"{exc} error for request method: {request.method} "
        f"url: {request.url} and body: {request.scope.get('body')}"
    )
    return await request_validation_exception_handler(request, exc)
