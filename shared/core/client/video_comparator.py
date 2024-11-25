from typing import List, Optional, Tuple, Type

from core.client.abstract.prediction_api_client import PredictionAPIClient
from core.path import LocalPath
from core.routes.base import BaseRoutes
from core.routes.video_comparator import routes
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
from core.schemas.modules.video_comparator import (
    VideoComparatorInput,
    VideoComparatorJobDocument,
    VideoComparatorJobResultsDocument,
    VideoComparatorOutput,
    VideoComparatorRealTimeInput,
    VideoComparatorRealTimeOutput,
    VideoComparatorSampleResultsDocument,
)


class VideoComparatorClient(PredictionAPIClient):
    InputSchema: Type[Input] = VideoComparatorInput
    OutputSchema: Type[Output] = VideoComparatorOutput
    RealTimeInputSchema: Type[RealTimeInput] = VideoComparatorRealTimeInput
    RealTimeOutputSchema: Type[RealTimeOutput] = VideoComparatorRealTimeOutput
    JobDocumentSchema: Type[JobDocument] = VideoComparatorJobDocument
    SampleResultsDocumentSchema: Type[SampleResultsDocument] = (
        VideoComparatorSampleResultsDocument
    )
    JobResultsDocumentSchema: Type[JobResultsDocument] = (
        VideoComparatorJobResultsDocument
    )
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
    ) -> VideoComparatorJobResultsDocument:
        return self.get_predictions_from_job_id(
            job_id=job_id,
            wait_if_not_existing=wait_if_not_existing,
            job_timeout=job_timeout,
        )

    def compare_videos_async(
        self,
        video_path_pairs: List[Tuple[str, str]],
        timeout: int = 60,
    ) -> List[VideoComparatorOutput]:
        return self.predict_async(
            samples=[
                LocalSample(paths=(LocalPath(video_path), LocalPath(other_video_path)))
                for (video_path, other_video_path) in video_path_pairs
            ],
            resource=(
                f"/{routes.VideoComparator.prefix}"
                f"{routes.VideoComparator.compare_videos}"
            ),
            timeout=timeout,
        )

    def compare_videos_sync(
        self,
        video_path_pairs: List[Tuple[str, str]],
        timeout: int = 60,
        job_timeout: int = 2700,
    ) -> List[VideoComparatorSampleResultsDocument]:
        return self.predict_sync(
            samples=[
                LocalSample(paths=(LocalPath(video_path), LocalPath(other_video_path)))
                for (video_path, other_video_path) in video_path_pairs
            ],
            resource=(
                f"/{routes.VideoComparator.prefix}"
                f"{routes.VideoComparator.compare_videos}"
            ),
            timeout=timeout,
            job_timeout=job_timeout,
        )

    def compare_videos_real_time(
        self,
        video_path: str,
        other_video_path: str,
        timeout: int = 2700,
    ) -> VideoComparatorRealTimeOutput:
        return self.predict_real_time(
            sample=LocalSample(
                paths=(LocalPath(video_path), LocalPath(other_video_path))
            ),
            resource=f"/{routes.VideoComparator.prefix}"
            f"{routes.VideoComparator.compare_videos_real_time}",
            timeout=timeout,
        )
