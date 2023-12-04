import logging
import os
import uuid
from typing import Dict, List, Optional, Tuple, Type, Union

import numpy as np
from core.google.storage_client import StorageClient
from core.packages.abstract.online_prediction_model.model_handler import (
    OnlinePredictionModelHandler,
)
from core.path import GSPath
from core.schemas.video_comparator import (
    InputSampleSchema as VideoComparatorInputSampleSchema,
)
from core.schemas.video_comparator import (
    OutputSampleSchema as VideoComparatorOutputSampleSchema,
)

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

    def create_new_model(self):
        return VideoComparatorModel()

    # def _get_input_sample_schema_from_data_sample(self, data_sample: dict):
    #     raise VideoComparatorInputSampleSchema.parse_obj(data_sample)

    def _get_input_sample_schema_class(self) -> Type[VideoComparatorInputSampleSchema]:
        return VideoComparatorInputSampleSchema

    def build_inference_args_kwargs_from_input_samples_schema(
        self, input_samples_schema: List[VideoComparatorInputSampleSchema]
    ) -> Tuple[Tuple, dict]:
        # sample = input_samples_schema[0]
        return (
            (),
            {
                "prediction_type": input_samples_schema[0].prediction_type,
                # "video": self._preprocess_video(sample.video),
                # "other_video": self._preprocess_video(sample.other_video)
                # if sample.other_video is not None
                # else None,
                "video_other_video_pairs": [
                    (
                        self._preprocess_video(input_sample_schema.video),
                        self._preprocess_video(input_sample_schema.other_video)
                        if input_sample_schema.other_video is not None
                        else None,
                    )
                    for input_sample_schema in input_samples_schema
                ],
                "batch_size": self.batch_size,
                "delete_videos_after_inference": True,
            },
        )

    # pylint: disable=arguments-differ
    def inference(
        self,
        # video: Union[str, np.ndarray],
        # other_video: Optional[Union[str, np.ndarray]],
        video_other_video_pairs: List[
            Tuple[Union[str, np.ndarray], Optional[Union[str, np.ndarray]]]
        ],
        prediction_type: str,
        batch_size: int = 128,
        delete_videos_after_inference: bool = True,
    ) -> list:
        predictions = []
        for video, other_video in video_other_video_pairs:
            predictions.append(
                super().inference(
                    video=video,
                    other_video=other_video,
                    prediction_type=prediction_type,
                    batch_size=batch_size,
                )
            )
            if isinstance(video, str) and delete_videos_after_inference:
                os.remove(video)
            if isinstance(other_video, str) and delete_videos_after_inference:
                os.remove(other_video)

        return predictions

    # pylint: disable=arguments-renamed
    def postprocess(
        self, predictions: Union[float, np.ndarray]
    ) -> List[VideoComparatorOutputSampleSchema]:
        return [
            VideoComparatorOutputSampleSchema(results=prediction)
            for prediction in predictions
        ]

    def handle(self, data: List[Dict], context) -> List[Dict[str, str]]:
        if len(data) > 1:
            raise ValueError(
                "The model does not currently manage batched predictions, i.e. "
                "more than one pair of videos, partly because a single pair "
                "monopolizes the GPU and takes a long time to process"
            )

        return super().handle(data=data, context=context)
        # return [
        #     {
        #         key: array_to_string(value) if isinstance(value, np.ndarray) else value
        #         for key, value in prediction.items()
        #     }
        #     for prediction in predictions
        # ]
