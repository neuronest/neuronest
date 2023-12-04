from typing import Dict, List, Optional, Union

import numpy as np
import pandas as pd
from pydantic import validator

from core.schemas.abstract import online_prediction_model
from core.serialization.dataframe import dataframe_from_string, dataframe_to_string
from core.serialization.image import image_from_string, image_to_string

PREDICTION_COLUMNS = [
    "x_min",
    "y_min",
    "x_max",
    "y_max",
    "score",
    "class_id",
    "class_name",
]

INPUT_SAMPLE_SCHEMA_IMAGE_TYPE_SERIALIZATION = ".jpg"


class InputSampleSchema(online_prediction_model.InputSampleSchema):
    image: Union[np.ndarray]
    labels_to_predict: Optional[List[str]] = None
    confidence_threshold: Optional[float] = None
    overridden_image_width: Optional[int] = None

    @property
    def metadata(
        self,
    ) -> Dict[str, Union[Optional[List[str]], Optional[float], Optional[int]]]:
        return {
            "labels_to_predict": self.labels_to_predict,
            "confidence_threshold": self.confidence_threshold,
            "overridden_image_width": self.overridden_image_width,
        }

    @property
    def metadata_filtered(self) -> Dict[str, Union[List[str], float, int]]:
        return {
            metadata_name: metadata_value
            for metadata_name, metadata_value in self.metadata.items()
            if metadata_value is not None
        }

    def serialized_attributes_dict(self):
        # image_to_string(
        #     frame=resized_batch_sample_image,
        #     extension=self.PREPROCESSING_IMAGE_TYPE,
        # )
        return {
            key: image_to_string(
                value, extension=INPUT_SAMPLE_SCHEMA_IMAGE_TYPE_SERIALIZATION
            )
            if key == "image"
            else value
            for key, value in self.dict().items()
        }

    @classmethod
    def from_serialized_attributes_dict(
        cls, serialized_attributes_dict: Dict
    ) -> "InputSampleSchema":

        return cls(
            **{
                key: image_from_string(value) if key == "image" else value
                for key, value in serialized_attributes_dict.items()
            }
        )


class InputSchema(online_prediction_model.InputSchema):
    samples: List[InputSampleSchema]

    # fixme: the InputSampleSchema structures are parsed and  # pylint: disable=W0511
    #  validated one by one, but the InputSchema structure  # pylint: disable=W0511
    #  which wraps them is never validated anywhere it seems to  # pylint: disable=W0511
    #  me and therefore the sample validator is never executed  # pylint: disable=W0511
    @validator("samples")
    # pylint: disable=no-self-argument
    def validate_metadata_batch_unicity(
        cls, samples: List[InputSampleSchema]
    ) -> List[InputSampleSchema]:
        if len(samples) == 0:
            return []

        first_sample = samples[0]
        first_sample_metadata_filtered = first_sample.metadata_filtered

        error_message = (
            "If some metadata is specified for one sample, it has to be "
            "equally specified for every samples"
        )

        if len(first_sample_metadata_filtered) == 0:
            if any(len(sample.metadata_filtered) > 0 for sample in samples):
                raise ValueError(error_message)

            return samples

        if any(
            sample.metadata_filtered != first_sample_metadata_filtered
            for sample in samples
        ):
            raise ValueError(error_message)

        return samples


class OutputSampleSchema(online_prediction_model.OutputSampleSchema):
    results: pd.DataFrame

    @validator("results")
    # pylint: disable=no-self-argument
    def validate_results(cls, results):
        if not isinstance(results, pd.DataFrame):
            raise ValueError(
                f"The expected return type is a pandas DataFrame, received a {cls}"
            )
        if not set(PREDICTION_COLUMNS) == set(results.columns):
            raise ValueError(
                f"The expected colums are {PREDICTION_COLUMNS}, "
                f"received a {results.columns}"
            )
        return results

    def serialized_attributes_dict(self) -> Dict:
        return {
            key: dataframe_to_string(value) if key == "results" else value
            for key, value in self.dict().items()
        }

    @classmethod
    def from_serialized_attributes_dict(
        cls, serialized_attributes_dict: Dict
    ) -> "OutputSampleSchema":

        return cls(
            **{
                key: dataframe_from_string(value) if key == "results" else value
                for key, value in serialized_attributes_dict.items()
            }
        )
