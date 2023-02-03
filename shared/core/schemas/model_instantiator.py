import base64
import json
from typing import Optional, Tuple, Union

from pydantic import BaseModel, validator


class InstantiateModelInput(BaseModel):
    model_name: str


class UninstantiateModelInput(BaseModel):
    model_name: str


class UninstantiateModelLogsConditionedInput(UninstantiateModelInput):
    default_messages: Tuple[str, ...] = ("received inference",)
    time_delta_override: Optional[int] = None  # in seconds


class PubSubUninstantiateModelLogsConditioned(BaseModel):
    data: UninstantiateModelLogsConditionedInput

    @validator("data", pre=True)
    # pylint: disable=no-self-argument
    def deserialize_and_check_data(
        cls, data: Union[str, UninstantiateModelLogsConditionedInput]
    ) -> UninstantiateModelLogsConditionedInput:
        if isinstance(data, str):
            data = UninstantiateModelLogsConditionedInput.parse_obj(
                json.loads(base64.b64decode(data))
            )

        return data


class UninstantiateModelOutput(BaseModel):
    message: str


class InstantiateModelOutput(BaseModel):
    message: str
