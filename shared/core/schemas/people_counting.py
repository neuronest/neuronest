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
    assets_ids: List[str]
    counted_videos_storage_paths: List[GSPath]


class PeopleCounterRealTimeOutput(BaseModel):
    detections: List[Detection]
    counted_video_storage_path: Optional[GSPath] = None


class VideosToCountBucketOutput(BaseModel):
    bucket: str


class FirestoreResultsCollectionOutput(BaseModel):
    collection: str


class PeopleCounterDocument(BaseModel):
    asset_id: str
    job_id: str
    detections: List[Detection]
    counted_video_storage_path: GSPath
