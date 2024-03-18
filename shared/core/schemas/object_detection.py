from typing import Dict, List, Optional, Union

import numpy as np
import pandas as pd
from pydantic import validator

from core.schemas.abstract import online_prediction_model

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
