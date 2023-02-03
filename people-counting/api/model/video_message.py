import logging
from typing import Optional

from pydantic import BaseModel

logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)


class MessageAttributes(BaseModel):
    googclient_schemaencoding: Optional[str] = None


class Data(BaseModel):
    job_id: str
    storage_path: str
    save_counted_video_in_storage: bool = False


class VideoMessage(BaseModel):
    data: Data
    attributes: Optional[MessageAttributes] = None
    messageId: Optional[str] = None
    message_id: Optional[str] = None
    publishTime: Optional[str] = None
    publish_time: Optional[str] = None
