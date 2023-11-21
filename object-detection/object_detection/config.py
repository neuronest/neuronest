from core.config_overriding import override_config_forbidden_characters
from omegaconf import OmegaConf

cfg = override_config_forbidden_characters(OmegaConf.load("config.yaml"))
