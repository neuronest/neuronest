from enum import Enum
from typing import List

from pydantic import BaseModel


class Device(str, Enum):
    CPU = "cpu"
    CUDA = "cuda"


class InputSchemaSample(BaseModel):
    data: str


class InputSchema(BaseModel):
    samples: List[InputSchemaSample]


class OutputSchemaSample(BaseModel):
    results: str
