import logging
from typing import Any, List, Optional, Tuple

import pandas as pd
from core.packages.abstract.online_prediction_model.model_handler import (
    OnlinePredictionModelHandler,
)
from core.schemas.object_detection import PREDICTION_COLUMNS
from core.schemas.object_detection import (
    InputSampleSchema as ObjectDetectionInputSampleSchema,
)
from core.schemas.object_detection import (
    OutputSampleSchema as ObjectDetectionOutputSampleSchema,
)
from imutils import resize

from object_detection.config import cfg

from object_detection.modules.model import ObjectDetectionModel  # isort:skip

logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)


class ObjectDetectionModelHandler(OnlinePredictionModelHandler):
    def __init__(
        self,
        *args,
        inner_model_type: Optional[str] = None,
        inner_model_name: Optional[str] = None,
        image_width: Optional[int] = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.inner_model_type = inner_model_type or cfg.model.inner_model_type
        self.inner_model_name = inner_model_name or cfg.model.inner_model_name
        self.image_width = image_width or cfg.model.image_width
        self.labels_to_predict: Optional[List[str]] = None
        self.confidence_threshold: Optional[float] = None

    def _fill_labels_to_predict(self, labels_to_predict: Optional[List[str]]):
        self.labels_to_predict = labels_to_predict

    def _fill_confidence_threshold(self, confidence_threshold: Optional[float]):
        self.confidence_threshold = confidence_threshold

    def _fill_image_width(self, overridden_image_width: Optional[int]):
        if overridden_image_width is not None:
            self.image_width = overridden_image_width

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

    def _get_input_sample_schema_class(self):
        return ObjectDetectionInputSampleSchema

    # def _get_input_sample_schema_from_data_sample(self, data_sample: dict):
    #     raise ObjectDetectionInputSampleSchema.parse_obj(data_sample)

    # def _batch_sample_to_input_sample_schema(
    #     self, image: np.ndarray
    # ) -> ObjectDetectionInputSampleSchema:
    #     return ObjectDetectionInputSampleSchema(image=image)

    def build_inference_args_kwargs_from_input_samples_schema(
        self, input_samples_schema: List[ObjectDetectionInputSampleSchema]
    ) -> Tuple[Tuple, dict]:

        first_sample_schema = input_samples_schema[0]

        self._fill_labels_to_predict(first_sample_schema.labels_to_predict)
        self._fill_confidence_threshold(first_sample_schema.confidence_threshold)
        self._fill_image_width(first_sample_schema.overridden_image_width)

        return (
            # (
            #     [
            #         resize(image_from_string(input_sample_schema.image), width=self.image_width)
            #         for input_sample_schema in input_samples_schema
            #     ],
            # ),
            (
                [
                    resize(input_sample_schema.image, width=self.image_width)
                    for input_sample_schema in input_samples_schema
                ],
            ),
            {},
        )

    def postprocess(
        self, predictions: List[Any]
    ) -> List[ObjectDetectionOutputSampleSchema]:
        filtered_predictions = self._filter_predictions(predictions)

        # return [
        #     ObjectDetectionOutputSchemaSample(
        #         results=array_to_string(prediction.values)
        #     )
        #     for prediction in filtered_predictions
        # ]
        return [
            ObjectDetectionOutputSampleSchema(
                results=pd.DataFrame(prediction.values, columns=PREDICTION_COLUMNS)
            )
            for prediction in filtered_predictions
        ]
