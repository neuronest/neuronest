import logging

from core.packages.abstract.online_prediction_model import config

#
# class Model(config.Model):
#     batch_size: int


class Config(config.Config):
    pass
    # model: Model


logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)

cfg = Config.read_yaml_file("detect_anything/config.yaml")
