import logging

from core.packages.abstract.online_prediction_model import config

# from omegaconf import OmegaConf


class Model(config.Model):
    inner_model_type: str
    inner_model_name: str
    image_width: int


class Config(config.Config):
    model: Model


logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)

cfg = Config.read_yaml_file("object_detection/config.yaml")
