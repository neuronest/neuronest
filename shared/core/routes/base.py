from abc import ABC

from pydantic import BaseModel, root_validator


class _BaseRoutes(ABC, BaseModel):
    api_tag: str = "api"
    service_name: str
    version_number: int = 1
    version_name: str = None
    prefix: str = None
    root: str = None

    # pre=False allows values to contain the attributes with default values
    @root_validator(pre=False)
    # pylint: disable=no-self-argument,unused-argument
    def populate_version_name_prefix_root(cls, values: dict) -> dict:
        values["version_name"] = f"v{values['version_number']}"
        values["prefix"] = f"/{values['api_tag']}/{values['version_name']}"
        values["root"] = f"/{values['service_name']}{values['prefix']}"
        return values
