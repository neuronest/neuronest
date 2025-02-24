from typing import List, Optional, Type

from core.client.abstract.prediction_api_client import PredictionAPIClient
from core.path import LocalPath
from core.routes.base import BaseRoutes
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
    SampleResultsDocumentSchema: Type[SampleResultsDocument] = (
        PeopleCounterSampleResultsDocument
    )
    JobResultsDocumentSchema: Type[JobResultsDocument] = PeopleCounterJobResultsDocument
    routes: BaseRoutes = routes

    def __init__(
        self,
        host: str,
        key_path: Optional[str] = None,
        project_id: Optional[str] = None,
    ):
        super().__init__(
            host=host,
            key_path=key_path,
            project_id=project_id,
        )

    def get_predictions_from_job_id(
        self,
        job_id: str,
        wait_if_not_existing: bool = False,
        job_timeout: int = 2700,
    ) -> PeopleCounterJobResultsDocument:
        return self._get_predictions_from_job_id(
            job_id=job_id,
            wait_if_not_existing=wait_if_not_existing,
            job_timeout=job_timeout,
        )

    def count_people_async(
        self,
        videos_paths: List[str],
        save_counted_videos_in_storage: bool = False,
        timeout: int = 120,
    ) -> List[PeopleCounterOutput]:
        return self.predict_async(
            samples=[
                LocalSample(paths=(LocalPath(video_path),))
                for video_path in videos_paths
            ],
            resource=(
                f"/{routes.PeopleCounter.prefix}{routes.PeopleCounter.count_people}"
            ),
            input_kwargs={"save_counted_videos": save_counted_videos_in_storage},
            timeout=timeout,
        )

    def count_people_sync(
        self,
        videos_paths: List[str],
        save_counted_videos_in_storage: bool = False,
        timeout: int = 120,
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
            input_kwargs={
                "save_counted_video": save_counted_video_in_storage,
                "enable_video_showing": enable_video_showing,
            },
            timeout=timeout,
        )
