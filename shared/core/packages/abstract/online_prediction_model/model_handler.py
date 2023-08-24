import logging
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Type

import torch
from ts.context import Context
from ts.torch_handler.base_handler import BaseHandler

from core.packages.abstract.online_prediction_model.modules.model import (
    OnlinePredictionModel,
)
from core.schemas.abstract.online_prediction_model import Device, OutputSchemaSample

# from core.schemas.object_detection import (
#     Device,
#     InputSampleSchema,
#     InputSchema,
#     OutputSchema,
# )

# a relative import should be done here as this module is intended to be used with
# torchserve
# pylint: disable=import-error
# from config import cfg  # isort:skip
# from object_detection.model import ObjectDetectionModel  # isort:skip

# pylint: enable=import-error

logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)


# See https://pytorch.org/serve/custom_service.html
# pylint: disable=too-many-instance-attributes
class OnlinePredictionModelHandler(BaseHandler, ABC):
    def __init__(
        self,
        # inner_model_type: str,
        # inner_model_name: str,
        # image_width: int,
        device: Device = Device.CUDA,
    ):
        super().__init__()
        self.device = device.value
        if device == Device.CUDA and not torch.cuda.is_available():
            logger.warning(f"GPU not detected while the asked device is {device.value}")
            self.device = Device.CPU.value
        else:
            self.device = device.value
        # self.inner_model_type = inner_model_type
        # self.inner_model_name = inner_model_name
        # self.image_width = image_width
        self._context = None
        # self.initialized = False
        self.model: Optional[OnlinePredictionModel] = None
        # self.labels_to_predict: Optional[List[str]] = None
        # self.confidence_threshold: Optional[float] = None

    # def _fill_labels_to_predict(self, labels_to_predict: Optional[List[str]]):
    #     self.labels_to_predict = labels_to_predict

    # def _fill_confidence_threshold(self, confidence_threshold: Optional[float]):
    #     self.confidence_threshold = confidence_threshold

    # def _fill_image_width(self, overridden_image_width: Optional[int]):
    #     if overridden_image_width is not None:
    #         self.image_width = overridden_image_width

    @staticmethod
    def get_input_schema_sample_class() -> Type:
        raise NotImplementedError

    @abstractmethod
    def get_inference_data_and_other_args_kwargs_from_input_schema_samples(
        self,
        input_schema_samples: List[Any],
    ) -> Tuple[Tuple, dict]:
        """
        Returns the data in the format expected by the model to predict,
        the arguments and the key arguments of the prediction function
        """
        raise NotImplementedError

    def preprocess(self, data: List) -> Tuple[Tuple, dict]:
        # pylint: disable=invalid-name
        InputSchemaSample = self.get_input_schema_sample_class()
        validated_input_schema_samples = [
            InputSchemaSample.parse_obj(sample) for sample in data
        ]

        # validated_data = InputSchema(
        #     samples=[InputSampleSchema.parse_obj(sample) for sample in data]
        # )

        # if len(validated_data.samples) == 0:
        #     return []

        # return validated_data.samples
        return self.get_inference_data_and_other_args_kwargs_from_input_schema_samples(
            validated_input_schema_samples
        )

    def _retrieve_model_path(self) -> str:
        properties = self._context.system_properties
        manifest = self._context.manifest

        model_dir = properties.get("model_dir")
        serialized_file = manifest["model"]["serializedFile"]

        return os.path.join(model_dir, serialized_file)

        # first_sample = validated_data.samples[0]

        # self._fill_labels_to_predict(first_sample.labels_to_predict)
        # self._fill_confidence_threshold(first_sample.confidence_threshold)
        # self._fill_image_width(first_sample.overridden_image_width)
        #
        # return [
        #     resize(image_from_string(sample.data), width=self.image_width)
        #     for sample in validated_data.samples
        # ]

    def inference(self, *args, **kwargs) -> List[Any]:
        with torch.no_grad():
            self.model.eval()
            results = self.model(*args, **kwargs)
        return results

    # def _filter_predictions(
    #     self, raw_predictions: List[pd.DataFrame]
    # ) -> List[pd.DataFrame]:
    #     filtered_predictions = raw_predictions
    #
    #     if self.labels_to_predict is not None:
    #         filtered_predictions = [
    #             filtered_prediction[
    #                 filtered_prediction.name.isin(self.labels_to_predict)
    #             ]
    #             for filtered_prediction in filtered_predictions
    #         ]
    #
    #     if self.confidence_threshold is not None:
    #         filtered_predictions = [
    #             filtered_prediction[
    #                 filtered_prediction.confidence >= self.confidence_threshold
    #             ]
    #             for filtered_prediction in filtered_predictions
    #         ]
    #
    #     return filtered_predictions

    # the data argument of the BaseHandler.postprocess function has been renamed
    # predictions for more clarity on the fact that the function necessarily takes
    # as input the result of the prediction part of the model
    @abstractmethod
    def postprocess(  # pylint: disable=arguments-renamed
        self, predictions: List[Any]
    ) -> List[OutputSchemaSample]:  # -> List[Dict[str, str]]:
        raise NotImplementedError
        # filtered_predictions = self._filter_predictions(data)
        #
        # return [
        #     OutputSchema(results=array_to_string(prediction.values)).dict()
        #     for prediction in filtered_predictions
        # ]

    def initialize_model_pt(self, context: Context):
        self._context = context

        model_pt_path = self._retrieve_model_path()

        if not os.path.isfile(model_pt_path):
            raise RuntimeError("The model.pt file is missing")

        # if self.device == Device.CUDA and not torch.cuda.is_available():
        #     logger.warning(f"GPU not detected while the device is {self.device}")
        #     self.device = Device.CPU.value

        # self.model = ObjectDetectionModel(
        #     model_type=self.inner_model_type, model_name=self.inner_model_name
        # ).load(model_pt_path)
        model_pt = OnlinePredictionModel.get_model_pt_from_path(
            model_pt_path=model_pt_path
        )
        # self.model = OnlinePredictionModel.
        # self.model.to(self.device)
        model_pt.to(self.device)
        return model_pt

        # self.initialized = True

    # @abstractmethod
    # def initialize(self, context: Context):
    #     """
    #     Initialize model. This will be called during model loading time
    #     :param context: Initial context contains model server system properties.
    #     :return:
    #     """
    #     raise NotImplementedError
    # self._context = context
    #
    # model_pt_path = self._retrieve_model_path()
    #
    # if not os.path.isfile(model_pt_path):
    #     raise RuntimeError("The model.pt file is missing")
    #
    # # if self.device == Device.CUDA and not torch.cuda.is_available():
    # #     logger.warning(f"GPU not detected while the device is {self.device}")
    # #     self.device = Device.CPU.value
    #
    # self.model = ObjectDetectionModel(
    #     model_type=self.inner_model_type, model_name=self.inner_model_name
    # ).load(model_pt_path)
    # # self.model = OnlinePredictionModel.
    # self.model.to(self.device)
    #
    # # self.initialized = True

    @abstractmethod
    def initialize_new_model(self):
        raise NotImplementedError

    def initialize(self, context: Context):
        """
        Initialize model. This will be called during model loading time
        :param context: Initial context contains model server system properties.
        :return:
        """
        self._context = context
        self.model = self.initialize_new_model()
        # self.model.set_model(model=self.initialize_model_pt(context=context))
        self.model.load(path=self._retrieve_model_path())
        self.model.to(self.device)

    def handle(self, data: List[Dict], context: Context) -> List[Dict[str, str]]:
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

        inference_data_and_other_args, inference_kwargs = self.preprocess(data=data)
        predictions = self.inference(*inference_data_and_other_args, **inference_kwargs)
        post_processed_predictions = self.postprocess(predictions)
        if not isinstance(post_processed_predictions, list):
            post_processed_predictions = [post_processed_predictions]
        return [output.dict() for output in post_processed_predictions]
