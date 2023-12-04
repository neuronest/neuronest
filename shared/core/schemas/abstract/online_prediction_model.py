from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List

from cachetools.func import ttl_cache
from pydantic import BaseModel


class Device(str, Enum):
    CPU = "cpu"
    CUDA = "cuda"


class InputSampleSchema(BaseModel, ABC):
    class Config:
        arbitrary_types_allowed = True

    @ttl_cache(ttl=60)
    @abstractmethod
    def serialized_attributes_dict(self) -> Dict[str, Any]:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def from_serialized_attributes_dict(
        cls, serialized_attributes_dict: Dict[str, Any]
    ) -> "InputSampleSchema":
        raise NotImplementedError


class InputSchema(BaseModel):
    samples: List[InputSampleSchema]


class OutputSampleSchema(BaseModel):
    results: Any

    class Config:
        arbitrary_types_allowed = True

    @abstractmethod
    def serialized_attributes_dict(self) -> Dict[str, Any]:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def from_serialized_attributes_dict(
        cls, serialized_attributes_dict: Dict[str, Any]
    ) -> "OutputSampleSchema":
        raise NotImplementedError
