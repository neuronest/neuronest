from typing import List, Optional, Union

from omegaconf import ListConfig
from pydantic import BaseModel, validator


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
