from typing import Optional, Tuple

from pydantic import BaseModel


class InstantiateModelInput(BaseModel):
    model_name: str


class UninstantiateModelInput(BaseModel):
    model_name: str


class UninstantiateModelLogsConditionedInput(UninstantiateModelInput):
    default_messages: Tuple[str, ...] = ("received inference",)
    time_delta_override: Optional[int] = None  # in seconds


class UninstantiateModelOutput(BaseModel):
    message: str


class InstantiateModelOutput(BaseModel):
    message: str
