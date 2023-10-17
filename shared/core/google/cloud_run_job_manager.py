from threading import Thread
from typing import List, Optional, Union

from google.cloud.exceptions import NotFound
from google.cloud.run_v2 import (
    CreateJobRequest,
    DeleteJobRequest,
    EnvVar,
    ExecutionsClient,
    Job,
    JobsClient,
    ListExecutionsRequest,
    ListJobsRequest,
    RunJobRequest,
    types,
)

from core.auth import get_credentials
from core.schemas.google.cloud_run import ExecutionSchema, JobConfig, JobSchema
from core.serialization.protobuf import protobuf_to_dict
from core.utils import hyphen_to_underscore


class CloudRunJobManager:
    def __init__(self, project_id: str, location: str, key_path: Optional[str] = None):
        self._credentials = (
            get_credentials(key_path=key_path) if key_path is not None else None
        )
        self._parent = f"projects/{project_id}/locations/{location}"
        self.jobs_client = JobsClient(credentials=self._credentials)
        self.executions_client = ExecutionsClient(credentials=self._credentials)
        self.project_id = project_id
        self.location = location

    @staticmethod
    def _ensure_unicity(jobs: List[JobSchema]) -> Optional[JobSchema]:
        if len(jobs) == 0:
            return None

        if len(jobs) > 1:
            raise ValueError("Multiple jobs found")

        return jobs[0]

    def list_executions(
        self, job_name: str, exclude_terminated: bool = False
    ) -> List[ExecutionSchema]:
        # noinspection PyTypeChecker
        request = ListExecutionsRequest(parent=f"{self._parent}/jobs/{job_name}")

        cloud_run_executions = [
            ExecutionSchema.parse_obj(protobuf_to_dict(execution))
            for execution in self.executions_client.list_executions(request=request)
        ]

        if exclude_terminated is False:
            return cloud_run_executions

        return [
            cloud_run_execution
            for cloud_run_execution in cloud_run_executions
            if cloud_run_execution.terminated_count == 0
        ]

    def run_job(self, job_name: str, sync: bool = False):
        # noinspection PyTypeChecker
        request = RunJobRequest(name=f"{self._parent}/jobs/{job_name}")
        func = self.jobs_client.run_job

        if sync is False:
            Thread(target=func, kwargs={"request": request}).start()

            return None

        return self.jobs_client.run_job(request=request)

    def list_jobs(
        self, job_name: Optional[str] = None, ensure_unicity: bool = False
    ) -> Union[List[JobSchema], Optional[JobSchema]]:
        # noinspection PyTypeChecker
        request = ListJobsRequest(parent=self._parent)

        cloud_run_jobs = [
            JobSchema.parse_obj(protobuf_to_dict(job))
            for job in self.jobs_client.list_jobs(request=request)
        ]

        if job_name is None:
            if ensure_unicity is True:
                return self._ensure_unicity(cloud_run_jobs)

            return cloud_run_jobs

        filtered_cloud_run_jobs = [
            cloud_run_job
            for cloud_run_job in cloud_run_jobs
            if hyphen_to_underscore(job_name) == cloud_run_job.name
        ]

        if ensure_unicity is True:
            return self._ensure_unicity(filtered_cloud_run_jobs)

        return filtered_cloud_run_jobs

    def delete_job(
        self, job_name: str, is_missing_ok: bool = False
    ) -> Optional[JobSchema]:
        # noinspection PyTypeChecker
        request = DeleteJobRequest(name=f"{self._parent}/jobs/{job_name}")

        try:
            operation = self.jobs_client.delete_job(request=request)
            response = operation.result()

        except NotFound as not_found:
            if is_missing_ok is True:
                return None

            raise not_found

        return JobSchema.parse_obj(protobuf_to_dict(response))

    def create_job(
        self,
        job_name: str,
        job_config: JobConfig,
        override_if_existing: bool = False,
    ) -> JobSchema:
        if override_if_existing is True:
            self.delete_job(job_name=job_name, is_missing_ok=True)

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
                    ),
                    task_count=job_config.task_count,
                    parallelism=job_config.parallelism,
                ),
                # mandatory for now, if removed, raise a 400 exception
                launch_stage="BETA",
            ),
            job_id=job_name,
        )

        operation = self.jobs_client.create_job(request=request)
        response = operation.result()

        return JobSchema.parse_obj(protobuf_to_dict(response))
