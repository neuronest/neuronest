from __future__ import annotations

import re
from datetime import datetime
from enum import Enum

from pydantic import BaseModel

from core.schemas.image_name import ImageName


class EvaluatedServiceName(str, Enum):
    PEOPLE_COUNTING = "people_counting"


class DatasetName(str):
    SUFFIX: str = "_dataset"
    REGEX: str = rf"^([a-z_]+){SUFFIX}$"

    @classmethod
    def from_service_name(cls, service_name: str) -> DatasetName:
        return cls(service_name + cls.SUFFIX)

    @classmethod
    def is_valid(cls, dataset_name: str) -> bool:
        matches = re.fullmatch(cls.REGEX, dataset_name)

        if matches is None:
            return False

        return matches.group(1) in list(EvaluatedServiceName)

    def __new__(cls, dataset_name, *args, **kwargs):
        if not cls.is_valid(dataset_name):
            raise ValueError(f"Incorrect dataset name: {dataset_name}")

        return str.__new__(cls, dataset_name, *args, **kwargs)

    def to_service_name(self) -> EvaluatedServiceName:
        return EvaluatedServiceName(re.fullmatch(self.REGEX, self).groups(1))


class EvaluateJobDocument(BaseModel):
    job_id: str
    job_date: datetime
    service_name: EvaluatedServiceName
    image_name: ImageName


class ServiceEvaluatorInput(BaseModel):
    reuse_already_computed_results: bool = True


class ServiceEvaluatorOutput(BaseModel):
    job_id: str