import logging

from core.packages.abstract.online_prediction_model import config

# from omegaconf import OmegaConf


class Model(config.Model):
    batch_size: int


class Config(config.Config):
    model: Model


logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)

cfg = Config.read_yaml_file("video_comparator/config.yaml")
