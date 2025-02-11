from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from database_api.api.dependencies import (  # get_database,
    handle_potential_cloud_sql_error,
)
from database_api.api.exceptions import (
    DatabaseStartingError,
    DatabaseStoppedError,
    DatabaseStoppingError,
)
from database_api.api.routes import router

# from migrations.alembic_command import upgrade_head
# from sqlalchemy import text


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


# @app.on_event("startup")
# async def startup_event():
#     database = next(get_database())
#     lock_or_migration_exception = None
#     release_lock_exception = None
#
#     try:
#         database.execute(text("SELECT pg_advisory_lock(123456);"))
#         print("Lock acquired, running alembic upgrade head...")
#         upgrade_head()
#     except Exception as exception:  # pylint: disable=broad-exception-caught
#         potential_cloud_sql_error = handle_potential_cloud_sql_error(
#             raise_error=False, on_error_correct=True
#         )
#         lock_or_migration_exception = potential_cloud_sql_error or exception
#     finally:
#         try:
#             database.execute(text("SELECT pg_advisory_unlock(123456);"))
#         except Exception as exception:  # pylint: disable=broad-exception-caught
#             potential_cloud_sql_error = handle_potential_cloud_sql_error(
#                 raise_error=False, on_error_correct=True
#             )
#             release_lock_exception = potential_cloud_sql_error or exception
#
#         # Raise exceptions in a proper order if they exist
#         if lock_or_migration_exception and release_lock_exception:
#             raise release_lock_exception from lock_or_migration_exception
#         if lock_or_migration_exception:
#             raise lock_or_migration_exception
#         if release_lock_exception:
#             raise release_lock_exception
#
#         print("Lock released.")
#
#     print("Alembic database migrations applied successfully.")


@app.middleware("http")
async def custom_error_handling_middleware(request: Request, call_next):
    """
    Middleware to catch and handle specific custom errors raised during request processing.
    """
    try:
        # Process the request
        response = await call_next(request)
        return response
    except (DatabaseStoppedError, DatabaseStoppingError):
        handle_potential_cloud_sql_error(raise_error=False, on_error_correct=True)
        # Handle the case when the database is stopped
        return JSONResponse(
            status_code=503,
            content="The database is currently stopped or stopping. "
            "It will restarted shortly, please try again shortly.",
        )
    except DatabaseStartingError:
        # Handle the case when the database is starting
        return JSONResponse(
            status_code=503,
            content="The database is currently starting. " "Please wait and try again.",
        )


if __name__ == "__main__":
    # used for debugging purposes only
    import uvicorn  # isort:skip

    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="debug")
