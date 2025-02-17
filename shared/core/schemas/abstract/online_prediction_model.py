from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, TypeVar

from pydantic import BaseModel


class Device(str, Enum):
    CPU = "cpu"
    CUDA = "cuda"


InputSampleSchema = TypeVar("InputSampleSchema", bound="BaseInputSampleSchema")
OutputSampleSchema = TypeVar("OutputSampleSchema", bound="BaseOutputSampleSchema")


class SchemaMixin(BaseModel, ABC):
    class Config:
        arbitrary_types_allowed = True

    @abstractmethod
    def serialize(self) -> Dict[str, Any]:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def deserialize(cls, serialized_attributes: Dict[str, Any]) -> SchemaMixin:
        raise NotImplementedError


class BaseInputSampleSchema(SchemaMixin, ABC):
    @classmethod
    @abstractmethod
    def deserialize(cls, serialized_attributes: Dict[str, Any]) -> InputSampleSchema:
        raise NotImplementedError


class BaseOutputSampleSchema(SchemaMixin, ABC):
    @classmethod
    @abstractmethod
    def deserialize(cls, serialized_attributes: Dict[str, Any]) -> OutputSampleSchema:
        raise NotImplementedError
