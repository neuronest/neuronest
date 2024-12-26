from __future__ import annotations

from typing import Any, ClassVar, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from pydantic import BaseModel, field_validator

from core.schemas.abstract.online_prediction_model import (
    BaseInputSampleSchema,
    BaseOutputSampleSchema,
)
from core.schemas.abstract.prediction_api_client import (
    BaseInput,
    BaseJobDocument,
    BaseJobResultsDocument,
    BaseOutput,
    BaseRealTimeInlineInput,
    BaseRealTimeOutput,
    BaseSampleResultsDocument,
)
from core.serialization.dataframe import dataframe_from_string, dataframe_to_string
from core.serialization.image import image_from_string, image_to_string

INPUT_SAMPLE_SCHEMA_IMAGE_TYPE_SERIALIZATION = ".jpg"


class OutputPrediction(BaseModel):
    x_min: int
    y_min: int
    x_max: int
    y_max: int
    score: float
    class_id: int
    class_name: str


class SampleMetadata(BaseModel):
    labels_to_predict: Optional[List[str]] = None
    confidence_threshold: Optional[float] = None
    overridden_image_width: Optional[int] = None


class ObjectDetectionInput(BaseInput):
    sample_metadata: SampleMetadata


class ObjectDetectionRealTimeInlineInput(BaseRealTimeInlineInput):
    sample_metadata: SampleMetadata


class ObjectDetectionOutput(BaseOutput):
    pass


class ObjectDetectionRealTimeOutput(BaseRealTimeOutput):
    predictions: List[OutputPrediction]


class ObjectDetectionJobDocument(BaseJobDocument):
    pass


class ObjectDetectionSampleResultsDocument(BaseSampleResultsDocument):
    predictions: List[OutputPrediction]


class ObjectDetectionJobResultsDocument(BaseJobResultsDocument):
    results: List[ObjectDetectionSampleResultsDocument]


class InputSampleSchema(BaseInputSampleSchema):
    image: np.ndarray
    sample_metadata: SampleMetadata

    IMAGE_FIELDS: ClassVar[Tuple[str, ...]] = ("image",)

    @property
    def metadata(
        self,
    ) -> Dict[str, Union[Optional[List[str]], Optional[float], Optional[int]]]:
        return {
            metadata_name: getattr(self, metadata_name)
            for metadata_name in SampleMetadata.model_fields
        }

    @property
    def metadata_filtered(self) -> Dict[str, Union[List[str], float, int]]:
        return {
            metadata_name: metadata_value
            for metadata_name, metadata_value in self.metadata.items()
            if metadata_value is not None
        }

    def serialize(self) -> Dict[str, Any]:
        return {
            key: (
                image_to_string(
                    value, extension=INPUT_SAMPLE_SCHEMA_IMAGE_TYPE_SERIALIZATION
                )
                if key in self.IMAGE_FIELDS
                else value
            )
            for key, value in self.model_dump().items()
        }

    @classmethod
    def deserialize(cls, serialized_attributes: Dict[str, Any]) -> InputSampleSchema:
        return cls(
            **{
                key: (image_from_string(value) if key in cls.IMAGE_FIELDS else value)
                for key, value in serialized_attributes.items()
            }
        )


class OutputSampleSchema(BaseOutputSampleSchema):
    results: pd.DataFrame

    @field_validator("results")
    @classmethod
    def validate_results(cls, results: pd.DataFrame) -> pd.DataFrame:
        prediction_columns = list(OutputPrediction.model_fields)

        if not set(prediction_columns) == set(results.columns):
            raise ValueError(
                f"The expected columns are {prediction_columns}, "
                f"received a {results.columns}"
            )

        return results

    def serialize(self) -> Dict[str, Any]:
        return {"results": dataframe_to_string(self.results)}

    @classmethod
    def deserialize(cls, serialized_attributes: Dict[str, Any]) -> OutputSampleSchema:
        return cls(
            **{"results": dataframe_from_string(serialized_attributes["results"])}
        )
