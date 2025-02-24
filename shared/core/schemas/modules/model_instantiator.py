from typing import Optional, Tuple

from pydantic import BaseModel


class InstantiateModelInput(BaseModel):
    # 'model_*' is a reserved Pydantic keyword, so we call it 'trained_model_name'
    trained_model_name: str


class UninstantiateModelInput(BaseModel):
    trained_model_name: str


class UninstantiateModelLogsConditionedInput(UninstantiateModelInput):
    default_messages: Tuple[str, ...] = ("received inference",)
    time_delta_override: Optional[int] = None  # in seconds


class UninstantiateModelOutput(BaseModel):
    message: str


class InstantiateModelOutput(BaseModel):
    message: str


class CloudSQLOutput(BaseModel):
    message: str


class CloudSQL(BaseModel):
    instance_name: str
