from typing import List, Optional, Tuple, Type

from core.client.abstract.prediction_api_client import PredictionAPIClient
from core.path import LocalPath
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
            samples_bucket_name=self._get_samples_bucket_name(),
            maximum_elements_number=self._get_maximum_elements_number(),
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
            samples_bucket_name=self._get_samples_bucket_name(),
            results_bucket_name=self._get_results_bucket_name(),
            job_collection_name=self._get_firestore_jobs_collection_name(),
            maximum_elements_number=self._get_maximum_elements_number(),
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
            samples_bucket_name=self._get_samples_bucket_name(),
            timeout=timeout,
        )
