import json
import logging
import typing

from fastapi import FastAPI, HTTPException, exception_handlers
from fastapi.exceptions import RequestValidationError
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request

from people_counting.api.routes import router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    main_app = FastAPI()
    main_app.include_router(router)

    main_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return main_app


app = create_app()


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
    return await exception_handlers.http_exception_handler(request, exc)


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
    return await exception_handlers.request_validation_exception_handler(request, exc)


if __name__ == "__main__":
    # used for debugging purposes only
    import uvicorn  # isort:skip

    uvicorn.run(app, host="0.0.0.0", port=8000)
