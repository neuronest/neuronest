import logging
import os
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import torch
from imutils import resize
from core.serialization.array import array_to_string
from core.serialization.image import image_from_string
from ts.context import Context
from ts.torch_handler.base_handler import BaseHandler

# a relative import should be done here as this module is intended to be used with
# torchserve
from config import cfg  # isort:skip
from model import ObjectDetectionModel  # isort:skip
from schemas import InputSchema, InputSampleSchema, OutputSchema  # isort:skip

logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)


# See https://pytorch.org/serve/custom_service.html
class ObjectDetectionModelHandler(BaseHandler):
    def __init__(
        self,
        device: str = "cpu",
        inner_model_type: Optional[str] = None,
        inner_model_name: Optional[str] = None,
        image_width: Optional[int] = None,
    ):
        super(ObjectDetectionModelHandler, self).__init__()
        self.device = device
        self.inner_model_type = inner_model_type or cfg.inner_model_type
        self.inner_model_name = inner_model_name or cfg.inner_model_name
        self.image_width = image_width or cfg.image_width
        self._context = None
        self.initialized = False
        self.model: Optional[ObjectDetectionModel] = None
        self.labels_to_predict: Optional[List[str]] = None
        self.confidence_threshold: Optional[float] = None

    def _retrieve_model_path(self) -> str:
        properties = self._context.system_properties
        manifest = self._context.manifest

        model_dir = properties.get("model_dir")
        serialized_file = manifest["model"]["serializedFile"]

        return os.path.join(model_dir, serialized_file)

    def _fill_labels_to_predict(self, labels_to_predict: Optional[List[str]]):
        self.labels_to_predict = labels_to_predict

    def _fill_confidence_threshold(self, confidence_threshold: Optional[float]):
        self.confidence_threshold = confidence_threshold

    def _fill_image_width(self, overridden_image_width: Optional[int]):
        if overridden_image_width is not None:
            self.image_width = overridden_image_width

    def initialize(self, context: Context):
        """
        Initialize model. This will be called during model loading time
        :param context: Initial context contains model server system properties.
        :return:
        """
        self._context = context

        model_pt_path = self._retrieve_model_path()

        if not os.path.isfile(model_pt_path):
            raise RuntimeError("The model.pt file is missing")

        self.model = ObjectDetectionModel(
            model_type=self.inner_model_type, model_name=self.inner_model_name
        ).load(model_pt_path)
        self.model.to(self.device)

        self.initialized = True

    def preprocess(self, data: List[Dict[str, str]]) -> List[np.ndarray]:
        validated_data = InputSchema(
            samples=[InputSampleSchema.parse_obj(sample) for sample in data]
        )

        if len(validated_data.samples) == 0:
            return []

        first_sample = validated_data.samples[0]

        self._fill_labels_to_predict(first_sample.labels_to_predict)
        self._fill_confidence_threshold(first_sample.confidence_threshold)
        self._fill_image_width(first_sample.overridden_image_width)

        return [
            resize(image_from_string(sample.data), width=self.image_width)
            for sample in validated_data.samples
        ]

    def inference(self, data: List[np.ndarray], *args, **kwargs) -> List[pd.DataFrame]:
        with torch.no_grad():
            self.model.eval()
            results = self.model(data, *args, **kwargs)

        return results

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

    def postprocess(self, raw_predictions: List[pd.DataFrame]) -> List[Dict[str, str]]:
        filtered_predictions = self._filter_predictions(raw_predictions)

        return [
            OutputSchema(results=array_to_string(prediction.values)).dict()
            for prediction in filtered_predictions
        ]

    def handle(
        self, data: List[Dict[str, str]], context: Context
    ) -> List[Dict[str, str]]:
        """
        Invoke by TorchServe for prediction request.
        Do pre-processing of data, prediction using model and postprocessing of
        prediction output.

        :param data: Input data for prediction
        :param context: Initial context contains model server system properties.
        :return: prediction output
        """
        if len(data) == 0:
            return []

        model_input = self.preprocess(data)
        model_output = self.inference(model_input)

        return self.postprocess(model_output)
