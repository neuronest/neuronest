from datetime import datetime
from typing import List, TypeVar

from pydantic import BaseModel

from core.path import GSPath

Input = TypeVar("Input", bound="BaseInput")
Output = TypeVar("Output", bound="BaseOutput")
RealTimeInput = TypeVar("RealTimeInput", bound="BaseRealTimeInput")
RealTimeOutput = TypeVar("RealTimeOutput", bound="BaseRealTimeOutput")


class JobDocument(BaseModel):
    job_id: str
    job_date: datetime
    assets_ids: List[str]
    one_result_per_job: bool


class BaseRealTimeIntput(BaseModel):
    element_storage_path: GSPath


class BaseInput(BaseModel):
    elements_storage_paths: List[GSPath]


class BaseRealTimeOutput(BaseModel):
    pass


class BaseOutput(BaseModel):
    job_id: str
