from abc import ABC

from pydantic import BaseModel, validator


class _BaseRoutes(ABC, BaseModel):
    service_name: str
    prefix: str = "/api/v1"
    root: str = None

    @validator("root", pre=True, always=True)
    # pylint: disable=no-self-argument,unused-argument
    def populate_root(cls, root: str, values: dict) -> str:
        service_name = values["service_name"]
        prefix = values["prefix"]

        return f"/{service_name}{prefix}"
