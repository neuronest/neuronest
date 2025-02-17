import logging
from typing import Any, List, Optional

import pandas as pd
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

    @staticmethod
    def _filter_predictions(
        raw_predictions: List[pd.DataFrame],
        batch_labels_to_predict: List[Optional[List[str]]],
        batch_confidence_thresholds: List[Optional[float]],
    ) -> List[pd.DataFrame]:
        filtered_predictions = raw_predictions

        filtered_predictions = [
            (
                filtered_prediction[filtered_prediction.name.isin(labels_to_predict)]
                if labels_to_predict is not None
                else filtered_prediction
            )
            for filtered_prediction, labels_to_predict in zip(
                filtered_predictions, batch_labels_to_predict
            )
        ]

        filtered_predictions = [
            (
                filtered_prediction[
                    filtered_prediction.confidence >= confidence_threshold
                ]
                if confidence_threshold is not None
                else filtered_prediction
            )
            for filtered_prediction, confidence_threshold in zip(
                filtered_predictions, batch_confidence_thresholds
            )
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
        images = [
            resize(sample.image, width=sample.sample_metadata.overridden_image_width)
            for sample in data
        ]

        raw_predictions = super().inference(data=images)

        return self._filter_predictions(
            raw_predictions=raw_predictions,
            batch_labels_to_predict=[
                sample.sample_metadata.labels_to_predict for sample in data
            ],
            batch_confidence_thresholds=[
                sample.sample_metadata.confidence_threshold for sample in data
            ],
        )

    def postprocess(self, data: List[Any]) -> List[ObjectDetectionOutputSampleSchema]:
        return [
            ObjectDetectionOutputSampleSchema(
                results=pd.DataFrame(
                    prediction.values, columns=list(OutputPrediction.model_fields)
                )
            )
            for prediction in data
        ]
