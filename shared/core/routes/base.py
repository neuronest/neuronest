from __future__ import annotations

from abc import ABC

from pydantic import BaseModel, model_validator


class _BaseRoutes(ABC, BaseModel):
    service_name: str
    api_tag: str = "api"
    version_number: int = 1
    version_name: str = None
    prefix: str = None
    root: str = None

    @model_validator
    def populate_version_name_prefix_root(self) -> _BaseRoutes:
        self.version_name = f"v{self.version_number}"
        self.prefix = f"/{self.api_tag}/{self.version_name}"
        self.root = f"/{self.service_name}{self.prefix}"

        return self


class BaseResources(ABC):
    prefix = "resources"
    firestore_jobs_collection: str = "/firestore_jobs_collection"
    maximum_elements_number: str = "/maximum_elements_number"
    samples_bucket: str = "/samples_bucket"
    results_bucket: str = "/results_bucket"
