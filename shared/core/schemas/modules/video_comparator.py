from __future__ import annotations

from typing import Dict, List, Optional, Union

import numpy as np
import typing_inspect
from pydantic import root_validator

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
from core.schemas.asset import VideoAsset
from core.serialization.array import array_from_string, array_to_string
from core.serialization.bytes import bytes_to_string, string_to_bytes
from core.services.asset_reader import make_asset_from_bytes
from core.utils import xor_not_none

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
    similarity_results: float


class VideoComparatorJobResultsDocument(BaseJobResultsDocument):
    results: List[VideoComparatorSampleResultsDocument]


class InputSampleSchema(BaseInputSampleSchema):
    video: Optional[VideoAsset] = None
    other_video: Optional[VideoAsset] = None
    video_embedding: Optional[np.ndarray] = None
    other_video_embedding: Optional[np.ndarray] = None

    @root_validator
    # pylint: disable=no-self-argument
    def check_specified_videos_consistency(
        cls, values: Dict[str, Union[Optional[VideoAsset], Optional[np.ndarray]]]
    ) -> Dict[str, Union[Optional[VideoAsset], Optional[np.ndarray]]]:
        video, other_video, video_embedding, other_video_embedding = (
            values.get("video"),
            values.get("other_video"),
            values.get("video_embedding"),
            values.get("other_video_embedding"),
        )

        if xor_not_none(video, video_embedding) is False:
            raise ValueError(
                "Either 'video' or 'video_embedding' must be specified, and not both"
            )

        if xor_not_none(other_video, other_video_embedding) is False:
            raise ValueError(
                "Either 'other_video' or 'other_video_embedding' must be specified, "
                "and not both"
            )

        return values

    def serialize(self) -> Dict[str, Optional[str]]:
        serialized_attributes_dict = {}

        for key, value in self.dict().items():
            if value is None:
                serialized_attributes_dict[key] = None
                continue
            if isinstance(value, np.ndarray):
                serialized_attributes_dict[key] = array_to_string(value)
                continue
            if isinstance(value, VideoAsset):
                serialized_attributes_dict[key] = bytes_to_string(
                    value.to_bytes(forced_extension=VIDEO_FORCED_EXTENSION)
                )

            raise NotImplementedError(f"Type of value not supported: {type(value)}")

        return serialized_attributes_dict

    @classmethod
    def deserialize(
        cls, serialized_attributes: Dict[str, Optional[str]]
    ) -> InputSampleSchema:
        deserialized_attributes_dict = {}

        for key, value in serialized_attributes.items():
            fields_with_types = cls.__fields__

            if key not in fields_with_types:
                raise ValueError(f"Unexpected field '{key}'")

            if value is None:
                deserialized_attributes_dict[key] = None
                continue
            if np.ndarray in typing_inspect.get_args(
                fields_with_types[key].type_, evaluate=True
            ):
                deserialized_attributes_dict[key] = array_from_string(value)
                continue
            if VideoAsset in typing_inspect.get_args(
                fields_with_types[key].type_, evaluate=True
            ):
                deserialized_attributes_dict[key] = make_asset_from_bytes(
                    string_to_bytes(value), extension=VIDEO_FORCED_EXTENSION
                )
                continue

            raise NotImplementedError(f"Type of value not supported: {type(value)}")

        return cls(**deserialized_attributes_dict)


class OutputSampleSchema(BaseOutputSampleSchema):
    video_embedding: np.ndarray
    other_video_embedding: np.ndarray
    similarity_results: float

    def serialize(self) -> Dict[str, Optional[str]]:
        serialized_attributes_dict = {}

        for key, value in self.dict().items():
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
            fields_with_types = cls.__fields__

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
