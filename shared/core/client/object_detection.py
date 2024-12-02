from typing import List, Optional, Type

import numpy as np

from core.client.abstract.prediction_api_client import PredictionAPIClient
from core.path import LocalPath
from core.routes.base import BaseRoutes
from core.routes.object_detection import routes
from core.schemas.abstract.prediction_api_client import (
    InlineSample,
    Input,
    JobDocument,
    JobResultsDocument,
    LocalSample,
    Output,
    RealTimeInlineInput,
    RealTimeOutput,
    SampleResultsDocument,
)
from core.schemas.modules.object_detection import (
    ObjectDetectionInput,
    ObjectDetectionJobDocument,
    ObjectDetectionJobResultsDocument,
    ObjectDetectionOutput,
    ObjectDetectionRealTimeInlineInput,
    ObjectDetectionRealTimeOutput,
    ObjectDetectionSampleResultsDocument,
    SampleMetadata,
)
from core.serialization.image import image_to_string


class ObjectDetectionClient(PredictionAPIClient):
    InputSchema: Type[Input] = ObjectDetectionInput
    OutputSchema: Type[Output] = ObjectDetectionOutput
    RealTimeInputSchema: Type[RealTimeInlineInput] = ObjectDetectionRealTimeInlineInput
    RealTimeOutputSchema: Type[RealTimeOutput] = ObjectDetectionRealTimeOutput
    JobDocumentSchema: Type[JobDocument] = ObjectDetectionJobDocument
    SampleResultsDocumentSchema: Type[SampleResultsDocument] = (
        ObjectDetectionSampleResultsDocument
    )
    JobResultsDocumentSchema: Type[JobResultsDocument] = (
        ObjectDetectionJobResultsDocument
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
    ) -> ObjectDetectionJobResultsDocument:
        return self._get_predictions_from_job_id(
            job_id=job_id,
            wait_if_not_existing=wait_if_not_existing,
            job_timeout=job_timeout,
        )

    def detect_objects_async(
        self,
        images_paths: List[str],
        labels_to_predict: Optional[List[str]] = None,
        confidence_threshold: Optional[float] = None,
        overridden_image_width: Optional[int] = None,
        timeout: int = 60,
    ) -> List[ObjectDetectionOutput]:
        return self.predict_async(
            samples=[
                LocalSample(paths=(LocalPath(image_path),))
                for image_path in images_paths
            ],
            resource=(
                f"/{routes.ObjectDetection.prefix}"
                f"{routes.ObjectDetection.detect_objects}"
            ),
            input_kwargs={
                "sample_metadata": {
                    "labels_to_predict": labels_to_predict,
                    "confidence_threshold": confidence_threshold,
                    "overridden_image_width": overridden_image_width,
                }
            },
            timeout=timeout,
        )

    def detect_objects_sync(
        self,
        images_paths: List[str],
        labels_to_predict: Optional[List[str]] = None,
        confidence_threshold: Optional[float] = None,
        overridden_image_width: Optional[int] = None,
        timeout: int = 60,
        job_timeout: int = 2700,
    ) -> List[ObjectDetectionSampleResultsDocument]:
        return self.predict_sync(
            samples=[
                LocalSample(paths=(LocalPath(image_path),))
                for image_path in images_paths
            ],
            resource=(
                f"/{routes.ObjectDetection.prefix}"
                f"{routes.ObjectDetection.detect_objects}"
            ),
            input_kwargs={
                "sample_metadata": {
                    "labels_to_predict": labels_to_predict,
                    "confidence_threshold": confidence_threshold,
                    "overridden_image_width": overridden_image_width,
                }
            },
            timeout=timeout,
            job_timeout=job_timeout,
        )

    def detect_objects_real_time(
        self,
        image: np.ndarray,
        labels_to_predict: Optional[List[str]] = None,
        confidence_threshold: Optional[float] = None,
        overridden_image_width: Optional[int] = None,
        timeout: int = 2700,
    ) -> ObjectDetectionRealTimeOutput:
        return self.predict_real_time_inline(
            sample=ObjectDetectionRealTimeInlineInput(
                inline_sample=InlineSample(element=image_to_string(image)),
                sample_metadata=SampleMetadata(
                    labels_to_predict=labels_to_predict,
                    confidence_threshold=confidence_threshold,
                    overridden_image_width=overridden_image_width,
                ),
            ),
            resource=f"/{routes.ObjectDetection.prefix}"
            f"{routes.ObjectDetection.detect_objects_real_time}",
            timeout=timeout,
        )
