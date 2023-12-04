from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Union

import numpy as np
from pydantic import BaseModel, validator

from core.path import GSPath
from core.schemas.abstract import online_prediction_model
from core.serialization.array import array_from_string, array_to_string


class PredictionType(str, Enum):
    VIDEO_FEATURES = "VIDEO_FEATURES"
    SIMILARITY = "SIMILARITY"


class InputSampleSchema(BaseModel):
    video: Union[GSPath, np.ndarray]
    other_video: Optional[Union[GSPath, np.ndarray]] = None
    prediction_type: PredictionType

    class Config:
        arbitrary_types_allowed = True

    @validator("video", "other_video")
    # pylint: disable=no-self-argument
    def validate_results(cls, video):
        if isinstance(video, str):
            return GSPath(video)
        if isinstance(video, np.ndarray):
            return video
        # if isinstance(video, str):
        #     return array_from_string(video)

        raise ValueError

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

    def serialized_attributes_dict(self) -> Dict:
        serialized_attributes_dict = {}
        for key, value in self.dict().items():
            if key not in ("video", "other_video"):
                serialized_attributes_dict[key] = value
                continue
            if isinstance(value, GSPath):
                serialized_attributes_dict[key] = value
                continue
            serialized_attributes_dict[key] = array_to_string(value)

        return serialized_attributes_dict

    @classmethod
    def from_serialized_attributes_dict(
        cls, serialized_attributes_dict: Dict
    ) -> "InputSampleSchema":
        deserialized_attributes_dict = {}
        for key, value in serialized_attributes_dict.items():
            if key not in ("video", "other_video"):
                serialized_attributes_dict[key] = value
                continue
            if GSPath.is_valid(value):
                deserialized_attributes_dict[key] = GSPath(value)
                continue
            deserialized_attributes_dict[key] = array_from_string(value)

        return cls(**deserialized_attributes_dict)


class InputSchema(online_prediction_model.InputSchema):
    samples: List[InputSampleSchema]


def is_castable_to_float(element: Any):
    try:
        # Attempt to cast the element to float
        float(element)
        # If successful, the element is castable to float
        return True
    except ValueError:
        # If an error occurs, it's an actual string
        return False


class OutputSampleSchema(online_prediction_model.OutputSampleSchema):
    results: Union[float, np.ndarray]

    @validator("results")
    # pylint: disable=no-self-argument
    def validate_results(cls, results):
        if isinstance(results, (float, np.ndarray)):
            return results

        raise ValueError(
            f"The expected return type is a float or a numpy, received a {cls}"
        )

    def serialized_attributes_dict(self) -> Dict:
        serialized_attributes_dict = {}
        for key, value in self.dict().items():
            if key != "results":
                serialized_attributes_dict[key] = value
                continue
            if is_castable_to_float(value):
                serialized_attributes_dict[key] = float(value)
                continue
            serialized_attributes_dict[key] = array_to_string(value)

        return serialized_attributes_dict

    @classmethod
    def from_serialized_attributes_dict(
        cls, serialized_attributes_dict: Dict
    ) -> "OutputSampleSchema":
        deserialized_attributes_dict = {}
        for key, value in serialized_attributes_dict.items():
            if key != "results":
                deserialized_attributes_dict[key] = value
                continue
            if is_castable_to_float(value):
                deserialized_attributes_dict[key] = float(value)
                continue
            deserialized_attributes_dict[key] = array_from_string(value)

        return cls(**deserialized_attributes_dict)
