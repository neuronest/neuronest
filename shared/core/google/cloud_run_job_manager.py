from uuid import uuid4

from google.cloud.run_v2 import (
    CreateJobRequest,
    EnvVar,
    Job,
    JobsClient,
    RunJobRequest,
    types,
)

from core.auth import get_credentials
from core.schemas.google.cloud_run import JobConfig, JobSchema
from core.serialization.protobuf import protobuf_to_dict
from core.utils import underscore_to_hyphen


class CloudRunJobManager:
    def __init__(self, key_path: str, project_id: str, location: str):
        self.client = JobsClient(credentials=get_credentials(key_path=key_path))
        self.project_id = project_id
        self.location = location
        self._parent = f"projects/{self.project_id}/locations/{self.location}"

    def run_job(self, job_name: str):
        # noinspection PyTypeChecker
        request = RunJobRequest(name=f"{self._parent}/jobs/{job_name}")

        self.client.run_job(request=request).result()

    def create_job(
        self,
        job_name: str,
        job_config: JobConfig,
    ) -> JobSchema:
        # noinspection PyTypeChecker
        request = CreateJobRequest(
            parent=self._parent,
            job=Job(
                template=types.ExecutionTemplate(
                    template=types.TaskTemplate(
                        containers=[
                            types.Container(
                                image=job_config.container_uri,
                                resources=types.ResourceRequirements(
                                    limits={
                                        "cpu": job_config.cpu,
                                        "memory": job_config.memory,
                                    },
                                ),
                                command=job_config.command,
                                args=job_config.command_args,
                                env=[
                                    EnvVar(
                                        name=environment_variable.name,
                                        value=environment_variable.value,
                                    )
                                    for environment_variable in (
                                        job_config.formatted_environment_variables
                                    )
                                ],
                            )
                        ],
                        max_retries=job_config.max_retries,
                        timeout=job_config.timeout,
                    )
                ),
                # mandatory for now, if removed, raise a 400 exception
                launch_stage="BETA",
            ),
            job_id=f"{underscore_to_hyphen(job_name)}-{str(uuid4())}",
        )

        operation = self.client.create_job(request=request)
        response = operation.result()

        return JobSchema.parse_obj(protobuf_to_dict(response))
