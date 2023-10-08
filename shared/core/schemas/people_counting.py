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
    videos_storage_paths: List[GSPath]
    save_counted_videos: bool = False


class PeopleCounterRealTimeInput(BaseModel):
    video_storage_path: GSPath
    save_counted_video: bool = False
    enable_video_showing: bool = False


class PeopleCounterOutput(BaseModel):
    job_id: str


class PeopleCounterRealTimeOutput(BaseModel):
    detections: List[Detection]
    counted_video_storage_path: Optional[GSPath] = None


class ResourcesOutput(BaseModel):
    resource: str


class PeopleCounterJobDocument(BaseModel):
    job_id: str
    assets_ids: List[str]


class PeopleCounterAssetResultsDocument(BaseModel):
    asset_id: str
    job_id: str
    detections: List[Detection]
    video_storage_path: GSPath
    counted_video_storage_path: Optional[GSPath] = None


class PeopleCounterJobResultsDocument(BaseModel):
    results: List[PeopleCounterAssetResultsDocument]
