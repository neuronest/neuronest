import base64
import json
import logging
from abc import ABC
from enum import Enum
from typing import List, Optional, Union

from pydantic import BaseModel, validator

logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)


class PubSubSubscriberPushMessageAttributes(BaseModel):
    googclient_schemaencoding: Optional[str] = None


class PubSubSubscriberPushMessage(ABC, BaseModel):
    data: BaseModel
    attributes: Optional[PubSubSubscriberPushMessageAttributes] = None
    messageId: Optional[str] = None
    message_id: Optional[str] = None
    publishTime: Optional[str] = None
    publish_time: Optional[str] = None

    @validator("data", pre=True)
    # pylint: disable=no-self-argument
    def deserialize_and_check_data(cls, data: Union[str, BaseModel]) -> BaseModel:
        if isinstance(data, str):
            # let pydantic deserialize to the correct class when known,
            # outside of the abstract class
            data = json.loads(base64.b64decode(data))
        return data


class PeopleCounterInputData(BaseModel):
    job_id: str
    storage_path: str
    save_counted_video_in_storage: bool = False


class PeopleCounterInput(PubSubSubscriberPushMessage):
    data: PeopleCounterInputData


class Direction(str, Enum):
    UP = "UP"
    DOWN = "DOWN"


class Detection(BaseModel):
    timestamp: float
    direction: Direction


class PeopleCounterOutput(BaseModel):
    detections: List[Detection]
    counted_video_storage_path: Optional[str] = None
