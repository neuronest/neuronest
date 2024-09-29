from datetime import datetime
from typing import List, Tuple, TypeVar

from pydantic import BaseModel

from core.path import GSPath, LocalPath

Input = TypeVar("Input", bound="BaseInput")
Output = TypeVar("Output", bound="BaseOutput")
RealTimeInput = TypeVar("RealTimeInput", bound="BaseRealTimeInput")
RealTimeOutput = TypeVar("RealTimeOutput", bound="BaseRealTimeOutput")
JobDocument = TypeVar("JobDocument", bound="BaseJobDocument")
SampleResultsDocument = TypeVar(
    "SampleResultsDocument", bound="BaseSampleResultsDocument"
)
JobResultsDocument = TypeVar("JobResultsDocument", bound="BaseJobResultsDocument")


class LocalSample(BaseModel):
    paths: Tuple[LocalPath, ...]


class GSSample(BaseModel):
    paths: Tuple[GSPath, ...]


class BaseJobDocument(BaseModel):
    job_id: str
    job_date: datetime
    samples_ids: List[str]


class BaseSampleResultsDocument(BaseModel):
    sample_id: str
    job_id: str


class BaseJobResultsDocument(BaseModel):
    results: List[BaseSampleResultsDocument]


class BaseRealTimeInput(BaseModel):
    sample: GSSample


class BaseInput(BaseModel):
    samples: List[GSSample]


class BaseRealTimeOutput(BaseModel):
    pass


class BaseOutput(BaseModel):
    job_id: str


class ResourcesOutput(BaseModel):
    resource: str
