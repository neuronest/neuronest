import logging
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel

from core.path import GSPath
from core.schemas.abstract.prediction_api_client import (
    BaseInput,
    BaseOutput,
    BaseRealTimeIntput,
    JobDocument,
    RealTimeOutput,
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


class PeopleCounterRealTimeInput(BaseRealTimeIntput):
    save_counted_video: bool = False
    enable_video_showing: bool = False


class PeopleCounterOutput(BaseOutput):
    pass


class PeopleCounterRealTimeOutput(RealTimeOutput):
    detections: List[Detection]
    counted_video_storage_path: Optional[GSPath] = None


class ResourcesOutput(BaseModel):
    resource: str


class PeopleCounterJobDocument(JobDocument):
    one_result_per_job: bool = True


class PeopleCounterAssetResultsDocument(BaseModel):
    asset_id: str
    job_id: str
    detections: List[Detection]
    video_storage_path: GSPath
    counted_video_storage_path: Optional[GSPath] = None


class PeopleCounterJobResultsDocument(BaseModel):
    results: List[PeopleCounterAssetResultsDocument]
