from abc import ABC
from typing import ClassVar

from pydantic import BaseModel


class _BaseRoutes(ABC, BaseModel):
    api_tag: ClassVar[str] = "api"
    service_name: str
    version_number: int = 1

    @property
    def version_name(self) -> str:
        return f"v{self.version_number}"

    @property
    def prefix(self) -> str:
        return f"/{self.api_tag}/{self.version_name}"

    @property
    def root(self) -> str:
        return f"/{self.service_name}{self.prefix}"
