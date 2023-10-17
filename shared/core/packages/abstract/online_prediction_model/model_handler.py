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

logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)


# See https://pytorch.org/serve/custom_service.html
# pylint: disable=too-many-instance-attributes
class OnlinePredictionModelHandler(BaseHandler, ABC):
    def __init__(
        self,
        device: Device = Device.CUDA,
    ):
        super().__init__()
        self.device = device.value
        if device == Device.CUDA and not torch.cuda.is_available():
            logger.warning(f"GPU not detected while the asked device is {device.value}")
            self.device = Device.CPU.value
        else:
            self.device = device.value
        self._context = None
        self.model: Optional[OnlinePredictionModel] = None

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
        input_schema_samples = [InputSchemaSample.parse_obj(sample) for sample in data]

        return self.get_inference_data_and_other_args_kwargs_from_input_schema_samples(
            input_schema_samples
        )

    def _retrieve_model_path(self) -> str:
        properties = self._context.system_properties
        manifest = self._context.manifest

        model_dir = properties.get("model_dir")
        serialized_file = manifest["model"]["serializedFile"]

        return os.path.join(model_dir, serialized_file)

    def inference(self, *args, **kwargs) -> List[Any]:
        with torch.no_grad():
            self.model.eval()
            results = self.model(*args, **kwargs)
        return results

    # the data argument of the BaseHandler.postprocess function has been renamed
    # predictions for more clarity on the fact that the function necessarily takes
    # as input the result of the prediction part of the model
    @abstractmethod
    def postprocess(  # pylint: disable=arguments-renamed
        self, predictions: List[Any]
    ) -> List[OutputSchemaSample]:  # -> List[Dict[str, str]]:
        raise NotImplementedError

    def initialize_model_pt(self, context: Context):
        self._context = context

        model_pt_path = self._retrieve_model_path()

        if not os.path.isfile(model_pt_path):
            raise RuntimeError("The model.pt file is missing")

        model_pt = OnlinePredictionModel.get_model_pt_from_path(
            model_pt_path=model_pt_path
        )
        model_pt.to(self.device)

        return model_pt

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
