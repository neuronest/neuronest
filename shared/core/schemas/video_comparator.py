from __future__ import annotations

from enum import Enum
from typing import List, Optional, Union

import numpy as np
from pydantic import BaseModel, validator

from core.path import GSPath
from core.schemas.abstract import online_prediction_model
from core.serialization.array import array_from_string, array_to_string


class PredictionType(str, Enum):
    VIDEO_FEATURES = "VIDEO_FEATURES"
    SIMILARITY = "SIMILARITY"


class InputSchemaSample(BaseModel):
    video: Union[GSPath, np.ndarray, str]
    other_video: Optional[Union[GSPath, np.ndarray, str]] = None
    prediction_type: PredictionType

    class Config:
        arbitrary_types_allowed = True

    @validator("video", "other_video")
    # pylint: disable=no-self-argument
    def validate_results(cls, video):
        if isinstance(video, GSPath):
            return video
        if isinstance(video, str):
            video = array_from_string(video)

        return video

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

    def to_serialized_dict(self):
        return {
            key: array_to_string(value) if isinstance(value, np.ndarray) else value
            for key, value in self.dict().items()
        }


class InputSchema(online_prediction_model.InputSchema):
    samples: List[InputSchemaSample]

    def to_serialized_dict(self):
        return {
            key: [
                InputSchemaSample.parse_obj(sample).to_serialized_dict()
                for sample in value
            ]
            if key == "samples"
            else value
            for key, value in self.dict().items()
        }


class OutputSchemaSample(online_prediction_model.OutputSchemaSample):
    results: Union[float, str, np.ndarray]

    class Config:
        arbitrary_types_allowed = True

    @validator("results")
    # pylint: disable=no-self-argument
    def validate_results(cls, results):
        if isinstance(results, str):
            results = array_from_string(results)

        return results
