from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, validator


class EnvironmentVariable(BaseModel):
    name: str
    value: str


class JobConfig(BaseModel):
    container_uri: str
    cpu: str
    memory: str
    max_retries: int = 0
    timeout: str = "2700s"
    task_count: int = 1
    parallelism: int = 1
    command: List[str] = Field(default_factory=list)
    command_args: List[str] = Field(default_factory=list)
    environment_variables: Dict[str, Optional[str]] = Field(default_factory=dict)
    # custom fields
    formatted_environment_variables: List[EnvironmentVariable] = Field(
        default_factory=list
    )

    @validator("formatted_environment_variables", always=True)
    # pylint: disable=no-self-argument,unused-argument
    def format_environment_variables(
        cls, formatted_environment_variables: List[EnvironmentVariable], values: dict
    ) -> List[EnvironmentVariable]:
        environment_variables = values["environment_variables"]

        return [
            EnvironmentVariable(
                name=environment_variable_name, value=environment_variable_value
            )
            for environment_variable_name, environment_variable_value in (
                environment_variables.items()
            )
            if environment_variable_value is not None
        ]


class JobSchema(BaseModel):
    name: str
    uid: str
    create_time: datetime
    update_time: datetime


class ExecutionSchema(BaseModel):
    name: str
    uid: str
    create_time: datetime
    update_time: datetime
    failed_count: int
    retried_count: int
    running_count: int
    succeeded_count: int
    cancelled_count: int

    @property
    def terminated_count(self) -> int:
        return self.succeeded_count + self.failed_count + self.cancelled_count
