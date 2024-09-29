from typing import List, Optional, Type

from core.client.abstract.prediction_api_client import PredictionAPIClient
from core.path import LocalPath
from core.routes.people_counting import routes
from core.schemas.abstract.prediction_api_client import (
    Input,
    JobDocument,
    JobResultsDocument,
    LocalSample,
    Output,
    RealTimeInput,
    RealTimeOutput,
    SampleResultsDocument,
)
from core.schemas.modules.people_counting import (
    PeopleCounterInput,
    PeopleCounterJobDocument,
    PeopleCounterJobResultsDocument,
    PeopleCounterOutput,
    PeopleCounterRealTimeInput,
    PeopleCounterRealTimeOutput,
    PeopleCounterSampleResultsDocument,
)


class PeopleCountingClient(PredictionAPIClient):
    InputSchema: Type[Input] = PeopleCounterInput
    OutputSchema: Type[Output] = PeopleCounterOutput
    RealTimeInputSchema: Type[RealTimeInput] = PeopleCounterRealTimeInput
    RealTimeOutputSchema: Type[RealTimeOutput] = PeopleCounterRealTimeOutput
    JobDocumentSchema: Type[JobDocument] = PeopleCounterJobDocument
    SampleResultsDocumentSchema: Type[
        SampleResultsDocument
    ] = PeopleCounterSampleResultsDocument
    JobResultsDocumentSchema: Type[JobResultsDocument] = PeopleCounterJobResultsDocument

    def __init__(
        self,
        host: str,
        key_path: Optional[str] = None,
        project_id: Optional[str] = None,
    ):
        super().__init__(
            host=host,
            key_path=key_path,
            root=routes.root,
            project_id=project_id,
        )

    def _get_results_bucket_name(self) -> str:
        return self._get_resource(
            resource=f"/{routes.Resources.prefix}{routes.Resources.results_bucket}"
        )

    def _get_firestore_jobs_collection_name(self) -> str:
        return self._get_resource(
            resource=f"/{routes.Resources.prefix}"
            f"{routes.Resources.firestore_jobs_collection}"
        )

    def _get_samples_bucket_name(self) -> str:
        return self._get_resource(
            resource=f"/{routes.Resources.prefix}{routes.Resources.samples_bucket}"
        )

    def _get_maximum_elements_number(self) -> int:
        return int(
            self._get_resource(
                resource=f"/{routes.Resources.prefix}"
                f"{routes.Resources.maximum_elements_number}"
            )
        )

    def get_predictions_from_job_id(
        self,
        job_id: str,
        wait_if_not_existing: bool = False,
        job_timeout: int = 2700,
    ) -> PeopleCounterJobResultsDocument:
        return self._get_predictions_from_job_id(
            results_bucket_name=self._get_results_bucket_name(),
            job_collection_name=self._get_firestore_jobs_collection_name(),
            job_id=job_id,
            wait_if_not_existing=wait_if_not_existing,
            job_timeout=job_timeout,
        )

    def count_people_async(
        self,
        videos_paths: List[str],
        save_counted_videos_in_storage: bool = False,
        timeout: int = 60,
    ) -> List[PeopleCounterOutput]:
        return self.predict_async(
            samples=[
                LocalSample(paths=(LocalPath(video_path),))
                for video_path in videos_paths
            ],
            resource=(
                f"/{routes.PeopleCounter.prefix}{routes.PeopleCounter.count_people}"
            ),
            samples_bucket_name=self._get_samples_bucket_name(),
            maximum_elements_number=self._get_maximum_elements_number(),
            input_kwargs={"save_counted_videos": save_counted_videos_in_storage},
            timeout=timeout,
        )

    def count_people_sync(
        self,
        videos_paths: List[str],
        save_counted_videos_in_storage: bool = False,
        timeout: int = 60,
        job_timeout: int = 2700,
    ) -> List[PeopleCounterSampleResultsDocument]:
        return self.predict_sync(
            samples=[
                LocalSample(paths=(LocalPath(video_path),))
                for video_path in videos_paths
            ],
            resource=(
                f"/{routes.PeopleCounter.prefix}{routes.PeopleCounter.count_people}"
            ),
            samples_bucket_name=self._get_samples_bucket_name(),
            results_bucket_name=self._get_results_bucket_name(),
            job_collection_name=self._get_firestore_jobs_collection_name(),
            maximum_elements_number=self._get_maximum_elements_number(),
            input_kwargs={"save_counted_videos": save_counted_videos_in_storage},
            timeout=timeout,
            job_timeout=job_timeout,
        )

    # used for debugging purposes only
    def count_people_real_time(
        self,
        video_path: str,
        save_counted_video_in_storage: bool = False,
        enable_video_showing: bool = False,
        timeout: int = 2700,
    ) -> PeopleCounterRealTimeOutput:
        return self.predict_real_time(
            sample=LocalSample(paths=(LocalPath(video_path),)),
            resource=f"/{routes.PeopleCounter.prefix}"
            f"{routes.PeopleCounter.count_people_real_time}",
            samples_bucket_name=self._get_samples_bucket_name(),
            input_kwargs={
                "save_counted_video": save_counted_video_in_storage,
                "enable_video_showing": enable_video_showing,
            },
            timeout=timeout,
        )
