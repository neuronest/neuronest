from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from service_evaluator.api.routes import router


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

if __name__ == "__main__":
    # used for debugging purposes only
    import uvicorn  # isort:skip

    uvicorn.run(app, host="0.0.0.0", port=8000)
