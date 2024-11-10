import logging

from core.packages.abstract.online_prediction_model import config
from pydantic import BaseModel


class App(BaseModel):
    maximum_elements_number: int


class Job(BaseModel):
    container_uri: str
    cpu: str
    memory: str


class Model(config.Model):
    batch_size: int


class Preprocessing(BaseModel):
    fps: int
    image_size: int
    center_crop_size: int


class Config(config.Config):
    app: App
    job: Job
    model: Model
    preprocessing: Preprocessing


logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)

cfg = Config.read_yaml_file("conf/config.yaml")
