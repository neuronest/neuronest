from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
from PIL import Image
from pydantic import BaseModel

from core.schemas.abstract import online_prediction_model
from core.serialization.array import array_from_string, array_to_string
from core.serialization.image import image_from_string, image_to_string

# class PredictionType(str, Enum):
#     VIDEO_FEATURES = "VIDEO_FEATURES"
#     SIMILARITY = "SIMILARITY"


INPUT_SAMPLE_SCHEMA_IMAGE_TYPE_SERIALIZATION = ".jpg"


class DetectAnythingPrediction(BaseModel):
    bbox: np.ndarray
    logit: np.ndarray
    phrase: str

    class Config:
        arbitrary_types_allowed = True

    # class Config:
    #     arbitrary_types_allowed = True
    #
    # @validator('bbox', 'logit', pre=True, each_item=True)
    # def check_bbox_logit_type(cls, bbox_or_logit, values, field, **kwargs):
    #     if isinstance(bbox_or_logit, torch.Tensor):
    #         return bbox_or_logit
    #
    #     raise TypeError(f"Expected {torch.Tensor} type, got {type(bbox_or_logit)}")

    def serialized_attributes_dict(self):
        return {
            key: array_to_string(value) if key in {"image", "logit"} else value
            for key, value in self.dict().items()
        }

    @classmethod
    def from_serialized_attributes_dict(
        cls, serialized_attributes_dict: Dict
    ) -> "DetectAnythingPrediction":

        return cls(
            **{
                key: array_from_string(value) if key in {"image", "logit"} else value
                for key, value in serialized_attributes_dict.items()
            }
        )


class DetectAnythingImagePredictions(BaseModel):
    predictions: List[DetectAnythingPrediction]
    annotated_image: Optional[Image.Image]

    class Config:
        arbitrary_types_allowed = True

    def serialized_attributes_dict(self):
        serialized_attributes_dict = {}
        for field_name in self.__fields__:
            field_value = getattr(self, field_name)

            if field_name == "predictions":
                serialized_attributes_dict[field_name] = [
                    element.serialized_attributes_dict() for element in field_value
                ]
            elif field_name == "annotated_image":
                serialized_attributes_dict[field_name] = (
                    array_to_string(np.array(field_value))
                    if field_value is not None
                    else field_value
                )
            else:
                serialized_attributes_dict[field_name] = field_value

        return serialized_attributes_dict

    @classmethod
    def from_serialized_attributes_dict(
        cls, serialized_attributes_dict: Dict
    ) -> "DetectAnythingImagePredictions":
        deserialized_attributes_dict = {}
        for key, value in serialized_attributes_dict.items():
            if key == "predictions":
                deserialized_attributes_dict[key] = [
                    DetectAnythingPrediction.from_serialized_attributes_dict(element)
                    for element in value
                ]
            elif key == "annotated_image":
                deserialized_attributes_dict[key] = (
                    Image.fromarray(array_from_string(value))
                    if value is not None
                    else value
                )
            else:
                deserialized_attributes_dict[key] = value

        return cls(**deserialized_attributes_dict)


class InputSampleSchema(BaseModel):
    rgb_image: np.ndarray
    texts_prompt: List[str]
    box_threshold: float
    text_threshold: float
    annotate_image: bool = False

    class Config:
        arbitrary_types_allowed = True

    # @validator("image")
    # # pylint: disable=no-self-argument
    # def validate_image(cls, image):
    #     if image
    #     if video is None:
    #         return None
    #     if isinstance(video, str):
    #         return GSPath(video)
    #     if isinstance(video, np.ndarray):
    #         return video
    #
    #     raise ValueError

    # @validator("prediction_type")
    # # pylint: disable=no-self-argument
    # def check_consistency_between_prediction_type_and_paths(
    #     cls, prediction_type, values
    # ):
    #     video = values.get("video")
    #     other_video = values.get("other_video")
    #     if prediction_type == PredictionType.SIMILARITY and (
    #         video is None or other_video is None
    #     ):
    #         raise ValueError(
    #             "Expected both video paths to be not None "
    #             "for the prediction type 'similarity'"
    #         )
    #     if prediction_type == PredictionType.VIDEO_FEATURES and (
    #         other_video is not None
    #     ):
    #         raise ValueError(
    #             "Expected only one video_path for the prediction type 'video_features'"
    #         )
    #     return prediction_type

    def serialized_attributes_dict(self):
        # image_to_string(
        #     frame=resized_batch_sample_image,
        #     extension=self.PREPROCESSING_IMAGE_TYPE,
        # )
        return {
            key: image_to_string(
                value, extension=INPUT_SAMPLE_SCHEMA_IMAGE_TYPE_SERIALIZATION
            )
            if key == "rgb_image"
            else value
            for key, value in self.dict().items()
        }

    @classmethod
    def from_serialized_attributes_dict(
        cls, serialized_attributes_dict: Dict
    ) -> "InputSampleSchema":

        return cls(
            **{
                key: image_from_string(value) if key == "rgb_image" else value
                for key, value in serialized_attributes_dict.items()
            }
        )


class InputSchema(online_prediction_model.InputSchema):
    samples: List[InputSampleSchema]


#
# def is_castable_to_float(element: Any):
#     try:
#         # Attempt to cast the element to float
#         float(element)
#         # If successful, the element is castable to float
#         return True
#     except (ValueError, TypeError):
#         return False


class OutputSampleSchema(online_prediction_model.OutputSampleSchema):
    results: DetectAnythingImagePredictions

    def serialized_attributes_dict(self) -> Dict:
        serialized_attributes_dict = {}
        for field_name in self.__fields__:
            field_value = getattr(self, field_name)

            if field_name == "results":
                serialized_attributes_dict[
                    field_name
                ] = field_value.serialized_attributes_dict()
            else:
                serialized_attributes_dict[field_name] = field_value

        return serialized_attributes_dict

    @classmethod
    def from_serialized_attributes_dict(
        cls, serialized_attributes_dict: Dict
    ) -> "OutputSampleSchema":
        deserialized_attributes_dict = {}
        for key, value in serialized_attributes_dict.items():
            if key == "results":
                deserialized_attributes_dict[
                    key
                ] = DetectAnythingImagePredictions.from_serialized_attributes_dict(
                    value
                )
            else:
                deserialized_attributes_dict[key] = value

        return cls(**deserialized_attributes_dict)
