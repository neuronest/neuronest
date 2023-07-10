import logging

from omegaconf import OmegaConf

logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)

cfg = OmegaConf.load("config.yaml")

for forbidden_character, replacement_character in zip(
    cfg.bigquery.dataset.forbidden_characters,
    cfg.bigquery.dataset.replacement_characters_of_forbidden_characters,
):
    if forbidden_character not in cfg.bigquery.dataset.name:
        continue
    cfg.bigquery.dataset.name = cfg.bigquery.dataset.name.replace(
        forbidden_character, replacement_character
    )
    logger.warning(
        f"We replace the forbidden character '{forbidden_character}' "
        f"with '{replacement_character}' for the element bigquery.dataset.name"
    )
