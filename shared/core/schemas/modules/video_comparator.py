from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
import typing_inspect

from core.path import GSPath
from core.schemas.abstract.online_prediction_model import (
    BaseInputSampleSchema,
    BaseOutputSampleSchema,
)
from core.schemas.abstract.prediction_api_client import (
    BaseInput,
    BaseJobDocument,
    BaseJobResultsDocument,
    BaseOutput,
    BaseRealTimeInput,
    BaseRealTimeOutput,
    BaseSampleResultsDocument,
)
from core.serialization.array import array_from_string, array_to_string

VIDEO_FORCED_EXTENSION: str = ".mp4"


class VideoComparatorInput(BaseInput):
    pass


class VideoComparatorRealTimeInput(BaseRealTimeInput):
    pass


class VideoComparatorOutput(BaseOutput):
    pass


class VideoComparatorRealTimeOutput(BaseRealTimeOutput):
    similarity_score: float


class VideoComparatorJobDocument(BaseJobDocument):
    pass


class VideoComparatorSampleResultsDocument(BaseSampleResultsDocument):
    similarity_score: float


class VideoComparatorJobResultsDocument(BaseJobResultsDocument):
    results: List[VideoComparatorSampleResultsDocument]


class InputSampleSchema(BaseInputSampleSchema):
    video_path: Optional[GSPath] = None
    other_video_path: Optional[GSPath] = None
    video_embedding: Optional[np.ndarray] = None
    other_video_embedding: Optional[np.ndarray] = None

    def serialize(self) -> Dict[str, Optional[str]]:
        serialized_attributes_dict = {}

        for key, value in self.model_dump().items():
            if value is None:
                serialized_attributes_dict[key] = None
                continue
            if isinstance(value, np.ndarray):
                serialized_attributes_dict[key] = array_to_string(value)
                continue
            if isinstance(value, GSPath):
                serialized_attributes_dict[key] = str(value)
                continue

            raise NotImplementedError(f"Type of value not supported: {type(value)}")

        return serialized_attributes_dict

    @classmethod
    def deserialize(
        cls, serialized_attributes: Dict[str, Optional[str]]
    ) -> InputSampleSchema:
        deserialized_attributes_dict = {}

        for key, value in serialized_attributes.items():
            fields_with_types = cls.model_fields

            if key not in fields_with_types:
                raise ValueError(f"Unexpected field '{key}'")

            if value is None:
                deserialized_attributes_dict[key] = None
                continue
            if fields_with_types[key].annotation in (Optional[np.ndarray], np.ndarray):
                deserialized_attributes_dict[key] = array_from_string(value)
                continue
            if fields_with_types[key].annotation in (Optional[GSPath], GSPath):
                deserialized_attributes_dict[key] = GSPath(value)
                continue

            raise NotImplementedError(f"Type of value not supported: {type(value)}")

        return cls(**deserialized_attributes_dict)


class OutputSampleSchema(BaseOutputSampleSchema):
    video_embedding: np.ndarray
    other_video_embedding: np.ndarray
    similarity_score: float

    def serialize(self) -> Dict[str, Optional[str]]:
        serialized_attributes_dict = {}

        for key, value in self.model_dump().items():
            if isinstance(value, float):
                serialized_attributes_dict[key] = value
                continue
            if isinstance(value, np.ndarray):
                serialized_attributes_dict[key] = array_to_string(value)
                continue

            raise NotImplementedError(f"Type of value not supported: {type(value)}")

        return serialized_attributes_dict

    @classmethod
    def deserialize(
        cls, serialized_attributes: Dict[str, Optional[str]]
    ) -> OutputSampleSchema:
        deserialized_attributes_dict = {}

        for key, value in serialized_attributes.items():
            fields_with_types = cls.model_fields

            if key not in fields_with_types:
                raise ValueError(f"Unexpected field '{key}'")

            if float in typing_inspect.get_args(
                fields_with_types[key].type_, evaluate=True
            ):
                deserialized_attributes_dict[key] = float(value)
                continue
            if np.ndarray in typing_inspect.get_args(
                fields_with_types[key].type_, evaluate=True
            ):
                deserialized_attributes_dict[key] = array_from_string(value)
                continue

            raise NotImplementedError(f"Type of value not supported: {type(value)}")

        return cls(**deserialized_attributes_dict)
