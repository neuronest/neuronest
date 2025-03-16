import logging
from typing import Optional

from google.cloud import scheduler_v1
from google.cloud.exceptions import NotFound

from core.client.abstract.base_client import BaseClient

logger = logging.getLogger(__name__)


class CloudSchedulerManager(BaseClient):
    def __init__(self, project_id: str, location: str, key_path: Optional[str] = None):
        super().__init__(key_path=key_path, project_id=project_id)
        self._parent = f"projects/{project_id}/locations/{location}"
        self.client = scheduler_v1.CloudSchedulerClient(credentials=self.credentials)
        self.location = location

    def pause_job(self, job_name: str):
        job_path = f"{self._parent}/jobs/{job_name}"

        try:
            job = self.client.get_job(name=job_path)
            if job.state == scheduler_v1.Job.State.PAUSED:
                logger.warning(f"Job {job_name} is already paused.")
                return

            self.client.pause_job(name=job_path)
            logger.info(f"Paused job: {job_name}")
        except NotFound:
            logger.error(f"Job {job_name} not found.")

    def resume_job(self, job_name: str):
        job_path = f"{self._parent}/jobs/{job_name}"

        try:
            job = self.client.get_job(name=job_path)
            if job.state == scheduler_v1.Job.State.ENABLED:
                logger.warning(f"Job {job_name} is already enabled.")
                return

            self.client.resume_job(name=job_path)
            logger.info(f"Resumed job: {job_name}")
        except NotFound:
            logger.error(f"Job {job_name} not found.")
