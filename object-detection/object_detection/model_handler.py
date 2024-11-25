import logging
from typing import Any, List, Optional

import pandas as pd
import torch
from core.packages.abstract.online_prediction_model.model_handler import (
    OnlinePredictionModelHandler,
)
from core.schemas.modules.object_detection import (
    InputSampleSchema as ObjectDetectionInputSampleSchema,
)
from core.schemas.modules.object_detection import OutputPrediction
from core.schemas.modules.object_detection import (
    OutputSampleSchema as ObjectDetectionOutputSampleSchema,
)
from imutils import resize

from object_detection.config import cfg

from object_detection.modules.model import ObjectDetectionModel  # isort:skip

logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)


class ObjectDetectionModelHandler(OnlinePredictionModelHandler):
    INPUT_SAMPLE_SCHEMA = ObjectDetectionInputSampleSchema
    OUTPUT_SAMPLE_SCHEMA = ObjectDetectionOutputSampleSchema

    def __init__(
        self,
        *args,
        inner_model_type: Optional[str] = None,
        inner_model_name: Optional[str] = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.inner_model_type = inner_model_type or cfg.model.inner_model_type
        self.inner_model_name = inner_model_name or cfg.model.inner_model_name
        self.labels_to_predict: Optional[List[str]] = None
        self.confidence_threshold: Optional[float] = None
        self.overridden_image_width: Optional[int] = None

    def _fill_labels_to_predict(self, labels_to_predict: Optional[List[str]]):
        self.labels_to_predict = labels_to_predict

    def _fill_confidence_threshold(self, confidence_threshold: Optional[float]):
        self.confidence_threshold = confidence_threshold

    def _fill_overridden_image_width(self, overridden_image_width: Optional[int]):
        self.overridden_image_width = overridden_image_width

    def _filter_predictions(
        self, raw_predictions: List[pd.DataFrame]
    ) -> List[pd.DataFrame]:
        filtered_predictions = raw_predictions

        if self.labels_to_predict is not None:
            filtered_predictions = [
                filtered_prediction[
                    filtered_prediction.name.isin(self.labels_to_predict)
                ]
                for filtered_prediction in filtered_predictions
            ]

        if self.confidence_threshold is not None:
            filtered_predictions = [
                filtered_prediction[
                    filtered_prediction.confidence >= self.confidence_threshold
                ]
                for filtered_prediction in filtered_predictions
            ]

        return filtered_predictions

    def create_new_model(self):
        return ObjectDetectionModel(
            model_type=self.inner_model_type,
            model_name=self.inner_model_name,
        )

    def inference(
        self, data: List[ObjectDetectionInputSampleSchema], *args, **kwargs
    ) -> List[Any]:
        first_sample_schema = data[0]

        self._fill_labels_to_predict(
            first_sample_schema.sample_metadata.labels_to_predict
        )
        self._fill_confidence_threshold(
            first_sample_schema.sample_metadata.confidence_threshold
        )
        self._fill_overridden_image_width(
            first_sample_schema.sample_metadata.overridden_image_width
        )

        images = [
            torch.from_numpy(resize(sample.image, width=self.overridden_image_width))
            for sample in data
        ]

        return super().inference(
            data=images,
            device=self.device,
        )

    def postprocess(self, data: List[Any]) -> List[ObjectDetectionOutputSampleSchema]:
        filtered_predictions = self._filter_predictions(data)

        return [
            ObjectDetectionOutputSampleSchema(
                results=pd.DataFrame(
                    prediction.values, columns=list(OutputPrediction.model_fields)
                )
            )
            for prediction in filtered_predictions
        ]
