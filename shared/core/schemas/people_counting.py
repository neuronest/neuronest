import logging
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel

from core.path import GSPath

logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)


class Direction(str, Enum):
    UP = "UP"
    DOWN = "DOWN"


class Detection(BaseModel):
    timestamp: float
    direction: Direction


class PeopleCounterInput(BaseModel):
    video_storage_path: GSPath
    save_counted_video: bool = False


class PeopleCounterOutput(BaseModel):
    job_id: str
    asset_id: str
    storage_path: GSPath
    counted_video_storage_path: Optional[GSPath] = None


class PeopleCounterDocument(PeopleCounterOutput):
    detections: List[Detection]


class PeopleCounterRealTimeOutput(BaseModel):
    detections: List[Detection]
