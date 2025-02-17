import logging
from typing import Optional

from core.packages.abstract.online_prediction_model import config
from core.schemas.image_name import ImageNameWithTag
from pydantic import BaseModel


class App(BaseModel):
    maximum_elements_number: int


class Job(BaseModel):
    container_uri: Optional[ImageNameWithTag]
    cpu: str
    memory: str


class Model(config.Model):
    inner_model_type: str
    inner_model_name: str
    image_width: int


class Config(config.Config):
    app: App
    job: Job
    model: Model


logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)

cfg = Config.read_yaml_file("conf/config.yaml")
