import logging
import os
import uuid
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
from core.google.storage_client import StorageClient
from core.packages.abstract.online_prediction_model.model_handler import (
    OnlinePredictionModelHandler,
)
from core.path import GSPath
from core.schemas.video_comparator import (
    InputSchemaSample as VideoComparatorInputSchemaSample,
)
from core.schemas.video_comparator import (
    OutputSchemaSample as VideoComparatorOutputSchemaSample,
)
from core.serialization.array import array_to_string

from video_comparator.config import cfg
from video_comparator.modules.model import VideoComparatorModel

logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)


class VideoComparatorModelHandler(OnlinePredictionModelHandler):
    def __init__(
        self,
        *args,
        batch_size: Optional[int] = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.batch_size = batch_size or cfg.model.batch_size
        self.storage_client = StorageClient()

    @staticmethod
    def get_input_sample_schema_class():
        return VideoComparatorInputSchemaSample

    def _preprocess_video(self, video: Union[GSPath, np.ndarray]):
        if isinstance(video, GSPath):
            video_path = str(uuid.uuid4())
            self.storage_client.download_blob_to_file(
                bucket_name=video.bucket,
                source_blob_name=video.blob_name,
                destination_file_name=video_path,
            )
            return video_path
        if isinstance(video, np.ndarray):
            return video
        raise ValueError

    def build_inference_args_kwargs_from_input_samples(
        self, input_samples: List[VideoComparatorInputSchemaSample]
    ) -> Tuple[Tuple, dict]:
        sample = input_samples[0]
        return (
            (),
            {
                "prediction_type": sample.prediction_type,
                "video": self._preprocess_video(sample.video),
                "other_video": self._preprocess_video(sample.other_video)
                if sample.other_video is not None
                else None,
                "batch_size": self.batch_size,
                "delete_videos_after_inference": True,
            },
        )

    # pylint: disable=arguments-differ
    def inference(
        self,
        video: Union[str, np.ndarray],
        other_video: Optional[Union[str, np.ndarray]],
        prediction_type: str,
        batch_size: int = 128,
        delete_videos_after_inference: bool = True,
    ) -> list:
        prediction = super().inference(
            video=video,
            other_video=other_video,
            prediction_type=prediction_type,
            batch_size=batch_size,
        )
        if isinstance(video, str) and delete_videos_after_inference:
            os.remove(video)
        if isinstance(other_video, str) and delete_videos_after_inference:
            os.remove(other_video)
        return prediction

    # pylint: disable=arguments-renamed
    def postprocess(
        self, prediction: Union[float, np.ndarray]
    ) -> VideoComparatorOutputSchemaSample:  # -> List[Dict[str, str]]:
        return VideoComparatorOutputSchemaSample(results=prediction)

    def create_new_model(self):
        return VideoComparatorModel()

    def handle(self, data: List[Dict], context) -> List[Dict[str, str]]:
        if len(data) > 1:
            raise ValueError(
                "The model does not currently manage batched predictions, i.e. "
                "more than one pair of videos, partly because a single pair "
                "monopolizes the GPU and takes a long time to process"
            )
        predictions = super().handle(data=data, context=context)
        return [
            {
                key: array_to_string(value) if isinstance(value, np.ndarray) else value
                for key, value in prediction.items()
            }
            for prediction in predictions
        ]
