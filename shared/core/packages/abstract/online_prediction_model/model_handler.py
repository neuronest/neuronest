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
from core.schemas.abstract.online_prediction_model import (
    Device,
    InputSampleSchema,
    OutputSampleSchema,
)

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

    def _retrieve_model_path(self) -> str:
        properties = self._context.system_properties
        manifest = self._context.manifest

        model_dir = properties.get("model_dir")
        serialized_file = manifest["model"]["serializedFile"]

        model_path = os.path.join(model_dir, serialized_file)

        if not os.path.isfile(model_path):
            raise RuntimeError(
                f"The model.pt file is missing at location: {model_path}"
            )

        return model_path

    def initialize(self, context: Context):
        """
        Initialize model. This will be called during model loading time
        :param context: Initial context contains model server system properties.
        :return:
        """
        self._context = context
        self.model = self.create_new_model()
        self.model.load(path=self._retrieve_model_path())
        self.model.to(self.device)

    @abstractmethod
    def create_new_model(self):
        raise NotImplementedError

    @abstractmethod
    def _get_input_sample_schema_class(self) -> Type[InputSampleSchema]:
        raise NotImplementedError(
            f"The class inherited from {InputSampleSchema} and used at runtime "
            f"must be known to know on which class exactly to call certain methods"
        )

    def _get_input_sample_schema_from_data_sample(self, data_sample: Dict):
        return self._get_input_sample_schema_class().from_serialized_attributes_dict(
            data_sample
        )

    @abstractmethod
    def build_inference_args_kwargs_from_input_samples_schema(
        self,
        input_samples_schema: List[InputSampleSchema],
    ) -> Tuple[Tuple, dict]:
        """
        Returns the data in the format expected by the model to predict,
        the arguments and the key arguments of the prediction function
        """
        raise NotImplementedError

    # pylint: disable=arguments-renamed
    def preprocess(self, data_samples: List[Dict]) -> Tuple[Tuple, Dict]:
        # pylint: disable=invalid-name
        input_samples_schema = [
            self._get_input_sample_schema_from_data_sample(data_sample)
            for data_sample in data_samples
        ]

        return self.build_inference_args_kwargs_from_input_samples_schema(
            input_samples_schema
        )

    def inference(self, *args, **kwargs) -> List[Any]:
        with torch.no_grad():
            self.model.eval()
            model_inferences = self.model(*args, **kwargs)
        return model_inferences

    # the data argument of the BaseHandler.postprocess function has been renamed
    # predictions for more clarity on the fact that the function necessarily takes
    # as input the result of the prediction part of the model
    @abstractmethod
    def postprocess(  # pylint: disable=arguments-renamed
        self, predictions: List[Any]
    ) -> List[OutputSampleSchema]:
        raise NotImplementedError

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

        inference_args, inference_kwargs = self.preprocess(data_samples=data)
        inferences = self.inference(*inference_args, **inference_kwargs)
        output_samples_schema = self.postprocess(inferences)
        # if not isinstance(output_samples, list):
        #     output_samples = [output_samples]
        return [
            output_sample.serialized_attributes_dict()
            for output_sample in output_samples_schema
        ]
