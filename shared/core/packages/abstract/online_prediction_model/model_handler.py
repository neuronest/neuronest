import logging
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type

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
    SchemaMixin,
)

logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)


# See https://pytorch.org/serve/custom_service.html
class OnlinePredictionModelHandler(BaseHandler, ABC):
    INPUT_SAMPLE_SCHEMA: Optional[Type[InputSampleSchema]] = None
    OUTPUT_SAMPLE_SCHEMA: Optional[Type[OutputSampleSchema]] = None

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
    def _validate_all_instance_of(
        elements: List[SchemaMixin], data_class: Type[SchemaMixin]
    ):
        for element in elements:
            if isinstance(element, data_class) is False:
                raise ValueError(
                    f"At least one element of the list is not an instance of "
                    f"{data_class}"
                )

    def _retrieve_model_path(self) -> str:
        properties = self._context.system_properties
        manifest = self._context.manifest

        model_dir: str = properties.get("model_dir")
        serialized_file: str = manifest["model"]["serializedFile"]

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

    def preprocess(self, data: List[Dict]) -> List[InputSampleSchema]:
        return [self.INPUT_SAMPLE_SCHEMA.deserialize(sample) for sample in data]

    def inference(self, data: List[Any], *args, **kwargs) -> List[Any]:
        with torch.no_grad():
            self.model.eval()
            # pylint: disable=protected-access
            model_device = next(self.model._model.parameters()).device
            logger.info(f"Model is running on: {model_device}")
            model_inferences = self.model(data=data, **kwargs)
        return model_inferences

    def postprocess(self, data: List[Any]) -> List[OutputSampleSchema]:
        return [self.OUTPUT_SAMPLE_SCHEMA.deserialize(sample) for sample in data]

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

        preprocessed_data = self.preprocess(data)
        logger.info(f"preprocessed_data 1 {preprocessed_data}")

        self._validate_all_instance_of(preprocessed_data, self.INPUT_SAMPLE_SCHEMA)

        predictions = self.inference(preprocessed_data)
        logger.info(f"predictions 1 {predictions}")
        postprocessed_predictions = self.postprocess(predictions)
        logger.info(f"postprocessed_predictions 1 {postprocessed_predictions}")

        self._validate_all_instance_of(
            postprocessed_predictions, self.OUTPUT_SAMPLE_SCHEMA
        )

        preprocessed_data = self.preprocess(data)
        logger.info(f"preprocessed_data 2 {preprocessed_data}")

        self._validate_all_instance_of(preprocessed_data, self.INPUT_SAMPLE_SCHEMA)

        predictions = self.inference(preprocessed_data)
        logger.info(f"predictions 2 {predictions}")
        postprocessed_predictions = self.postprocess(predictions)
        logger.info(f"postprocessed_predictions 2 {postprocessed_predictions}")

        self._validate_all_instance_of(
            postprocessed_predictions, self.OUTPUT_SAMPLE_SCHEMA
        )

        return [sample.serialize() for sample in postprocessed_predictions]
