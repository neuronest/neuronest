from __future__ import annotations

from typing import Dict, List, Optional, Union

from omegaconf import ListConfig
from pydantic import BaseModel, root_validator, validator

from core.utils import hyphen_to_underscore, underscore_to_hyphen


class TrainingConfig(BaseModel):
    container_uri: str
    machine_type: str
    replica_count: int = 1
    accelerator_type: str = "ACCELERATOR_TYPE_UNSPECIFIED"
    accelerator_count: int = 0


class ServingModelUploadConfig(BaseModel):
    container_uri: str
    predict_route: str
    health_route: str
    ports: List[int]

    @validator("ports", pre=True)
    # pylint: disable=no-self-argument
    def validate_ports(cls, ports: Union[ListConfig, List[int]]) -> List[int]:
        return list(ports)


class ServingDeploymentConfig(BaseModel):
    machine_type: str = "n1-standard-2"
    min_replica_count: int = 1
    max_replica_count: int = 1
    accelerator_type: Optional[str] = None
    accelerator_count: int = 0

    @root_validator
    # pylint: disable=no-self-argument
    def validate_accelerator_fields(cls, values: dict) -> dict:
        """
        To disable GPUs during serving, the proper configuration is and only is:
            accelerator_type=None
            accelerator_count=0

        In the case where accelerator_type=ACCELERATOR_TYPE_UNSPECIFIED, we set it to
        None, and set accelerator_count to 0.
        Similarly, if accelerator_count=0, we set accelerator_type to None.
        """
        if (
            values["accelerator_type"] is None
            or values["accelerator_type"].lower() == "accelerator_type_unspecified"
        ):
            values["accelerator_count"] = 0
            values["accelerator_type"] = None

        if values["accelerator_count"] == 0:
            values["accelerator_type"] = None

        return values

    @classmethod
    def from_labels(cls, config_as_labels: Dict[str, str]) -> ServingDeploymentConfig:
        config_as_labels = {
            hyphen_to_underscore(key): value if value != "None" else None
            for key, value in config_as_labels.items()
        }

        config_as_labels["accelerator_type"] = hyphen_to_underscore(
            config_as_labels["accelerator_type"]
        ).upper()

        return cls(**config_as_labels)

    def as_labels(self) -> Dict[str, str]:
        # see https://goo.gl/xmQnxf for compatibility rules
        return {
            underscore_to_hyphen(key): underscore_to_hyphen(str(value)).lower()
            for key, value in self.dict().items()
        }
