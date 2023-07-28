import logging
from typing import List, Optional

import yaml

# from omegaconf import OmegaConf
from pydantic import BaseModel, validator

logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)


class Model(BaseModel):
    name: Optional[str]


class Training(BaseModel):
    container_uri: Optional[str]
    machine_type: str
    accelerator_type: str
    accelerator_count: int
    replica_count: int


class ServingModelUpload(BaseModel):
    container_uri: Optional[str]
    predict_route: str
    health_route: str
    ports: List[int]


class ServingDeployment(BaseModel):
    machine_type: str
    accelerator_type: str
    accelerator_count: int
    min_replica_count: int
    max_replica_count: int


class Dataset(BaseModel):
    name: str

    @validator("name")
    # pylint: disable=no-self-argument
    def validate_name(cls, name):
        forbidden_characters = ["-"]
        replacement_characters_of_forbidden_characters = ["_"]
        for forbidden_character, replacement_character in zip(
            forbidden_characters,
            replacement_characters_of_forbidden_characters,
        ):
            if forbidden_character not in name:
                continue

            name = name.replace(forbidden_character, replacement_character)
            logger.warning(
                f"We replace the forbidden character '{forbidden_character}' "
                f"with '{replacement_character}' for the element bigquery.dataset.name"
            )

        return name


class Bigquery(BaseModel):
    dataset: Dataset


class Config(BaseModel):
    project_id: str
    region: str
    service_account: str
    name: str
    package_name: str
    model: Model
    training: Training
    serving_model_upload: ServingModelUpload
    serving_deployment: ServingDeployment
    bigquery: Bigquery

    @classmethod
    def read_yaml_file(cls, file_path: str):
        with open(file_path, "r") as self_reader:
            yaml_data = yaml.safe_load(self_reader)
        return cls.parse_obj(yaml_data)


# cfg = OmegaConf.load("config.yaml")
cfg = Config.read_yaml_file("core/packages/online_prediction_model/config.yaml")

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
