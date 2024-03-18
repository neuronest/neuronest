from __future__ import annotations

from enum import Enum
from typing import Optional

import numpy as np
from pydantic import root_validator, validator

from core.path import GSPath
from core.serialization.schema import Schema


class PredictionType(str, Enum):
    VIDEO_FEATURES = "VIDEO_FEATURES"
    SIMILARITY = "SIMILARITY"


class Video(Schema):
    path: Optional[GSPath] = None
    array: Optional[np.ndarray] = None

    # validates whole model, before other validations occur
    @root_validator(pre=True)
    # pylint: disable=no-self-argument
    def check_path_and_array(cls, video):
        video_path, video_array = video.get("path"), video.get("array")
        if video_path is None and video_array is None:
            raise ValueError("Both path and array cannot be None")
        if video_path is not None and video_array is not None:
            raise ValueError("One of path and array has to be None")

        return video


class InputSampleSchema(Schema):
    video: Video
    other_video: Optional[Video] = None
    prediction_type: PredictionType

    @validator("prediction_type")
    # pylint: disable=no-self-argument
    def check_consistency_between_prediction_type_and_paths(
        cls, prediction_type, values
    ):
        video = values.get("video")
        other_video = values.get("other_video")
        if prediction_type == PredictionType.SIMILARITY and (
            video is None or other_video is None
        ):
            raise ValueError(
                "Expected both video paths to be not None "
                "for the prediction type 'similarity'"
            )
        if prediction_type == PredictionType.VIDEO_FEATURES and (
            other_video is not None
        ):
            raise ValueError(
                "Expected only one video_path for the prediction type 'video_features'"
            )
        return prediction_type


class OutputSampleSchema(Schema):
    video_vector: Optional[np.ndarray]
    similarity: Optional[float]
