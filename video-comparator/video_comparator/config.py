import logging

from core.packages.abstract.online_prediction_model import config

# from omegaconf import OmegaConf


class Model(config.Model):
    batch_size: int


class Config(config.Config):
    model: Model


logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)

# cfg = OmegaConf.load("object_detection/config.yaml")
cfg = Config.read_yaml_file("video_comparator/config.yaml")

# for forbidden_character, replacement_character in zip(
#     cfg.bigquery.dataset.forbidden_characters,
#     cfg.bigquery.dataset.replacement_characters_of_forbidden_characters,
# ):
#     if forbidden_character not in cfg.bigquery.dataset.name:
#         continue
#     cfg.bigquery.dataset.name = cfg.bigquery.dataset.name.replace(
#         forbidden_character, replacement_character
#     )
#     logger.warning(
#         f"We replace the forbidden character '{forbidden_character}' "
#         f"with '{replacement_character}' for the element bigquery.dataset.name"
#     )
