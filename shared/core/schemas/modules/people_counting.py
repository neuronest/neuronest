import logging
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel

from core.path import GSPath
from core.schemas.abstract.prediction_api_client import (
    BaseInput,
    BaseJobDocument,
    BaseJobResultsDocument,
    BaseOutput,
    BaseRealTimeInput,
    BaseRealTimeOutput,
    BaseSampleResultsDocument,
)

logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)


class Direction(str, Enum):
    UP = "UP"
    DOWN = "DOWN"


class Detection(BaseModel):
    timestamp: float
    direction: Direction


class PeopleCounterInput(BaseInput):
    save_counted_videos: bool = False


class PeopleCounterRealTimeInput(BaseRealTimeInput):
    save_counted_video: bool = False
    enable_video_showing: bool = False


class PeopleCounterOutput(BaseOutput):
    pass


class PeopleCounterRealTimeOutput(BaseRealTimeOutput):
    detections: List[Detection]
    counted_video_storage_path: Optional[GSPath] = None


class PeopleCounterJobDocument(BaseJobDocument):
    pass


class PeopleCounterSampleResultsDocument(BaseSampleResultsDocument):
    detections: List[Detection]
    video_storage_path: GSPath
    counted_video_storage_path: Optional[GSPath] = None


class PeopleCounterJobResultsDocument(BaseJobResultsDocument):
    results: List[PeopleCounterSampleResultsDocument]
