from __future__ import annotations

from enum import Enum
from typing import List, Optional, Union

from pydantic import BaseModel, validator

from core.path import GSPath
from core.schemas.abstract import online_prediction_model


class PredictionType(str, Enum):
    VIDEO_FEATURES = "VIDEO_FEATURES"
    SIMILARITY = "SIMILARITY"


class InputSchemaSample(BaseModel):
    video_path: GSPath
    other_video_path: Optional[GSPath] = None
    prediction_type: PredictionType

    @validator("prediction_type")
    # pylint: disable=no-self-argument
    def check_consistency_between_prediction_type_and_paths(
        cls, prediction_type, values
    ):
        video_path = values.get("video_path")
        other_video_path = values.get("other_video_path")
        if prediction_type == PredictionType.SIMILARITY and (
            video_path is None or other_video_path is None
        ):
            raise ValueError(
                "Expected both video paths to be not None "
                "for the prediction type 'similarity'"
            )
        if prediction_type == PredictionType.VIDEO_FEATURES and (
            other_video_path is not None
        ):
            raise ValueError(
                "Expected only one video_path for the prediction type 'video_features'"
            )
        return prediction_type


class InputSchema(online_prediction_model.InputSchema):
    samples: List[InputSchemaSample]

    @validator("samples")
    # pylint: disable=no-self-argument
    def validate_samples(cls, samples):
        if len(samples) != 1:
            raise ValueError("number samples pre prediction should be exactly one")
        return samples


class OutputSchema(online_prediction_model.OutputSchema):
    results: Union[List[float], List[List[float]]]
