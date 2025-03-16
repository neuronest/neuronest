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

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


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

        logger.info(f"Retrieving model from path: {model_path}")

        if not os.path.isfile(model_path):
            raise RuntimeError(
                f"The model.pt file is missing at location: {model_path}"
            )

        return model_path

    def initialize(self, context: Context):
        self._context = context
        logger.info("Initializing model...")
        self.model = self.create_new_model()
        model_path = self._retrieve_model_path()
        self.model.load(path=model_path)
        self.model.to(self.device)
        logger.info("Model successfully loaded and moved to device.")

    @abstractmethod
    def create_new_model(self):
        raise NotImplementedError

    def preprocess(self, data: List[Dict]) -> List[InputSampleSchema]:
        logger.info(f"Preprocessing input data: {data}")
        return [self.INPUT_SAMPLE_SCHEMA.deserialize(sample) for sample in data]

    def inference(self, data: List[Any], *args, **kwargs) -> List[Any]:
        with torch.no_grad():
            self.model.eval()
            model_device = next(self.model._model.parameters()).device
            logger.info(f"Inference model is running on: {model_device}")
            logger.info(f"Inference data samples: {len(data)}")

            # Check and log the device of the input data
            if isinstance(data, torch.Tensor):
                data_device = data.device
                logger.info(f"Inference data is on device: {data_device}")
            elif isinstance(data, list) and isinstance(data[0], torch.Tensor):
                data_devices = {tensor.device for tensor in data}
                logger.info(f"Inference data is on devices: {data_devices}")
            else:
                logger.warning(
                    "Inference data is not a tensor or a list of tensors; device info unavailable.")

            # Run inference
            model_inferences = self.model(data=data, **kwargs)

            logger.info(f"Inference results: {model_inferences}")

        return model_inferences

    def postprocess(self, data: List[Any]) -> List[OutputSampleSchema]:
        logger.info(f"Postprocessing data: {data}")
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

        logger.info(f"handle data: {data}")
        logger.info(f"handle data samples: {len(data)}")
        preprocessed_data = self.preprocess(data)
        logger.info(f"handle preprocessed_data: {preprocessed_data}")
        logger.info(f"handle preprocessed_data samples: {len(preprocessed_data)}")

        self._validate_all_instance_of(preprocessed_data, self.INPUT_SAMPLE_SCHEMA)

        predictions = self.inference(preprocessed_data)
        logger.info(f"predictions data: {predictions}")
        logger.info(f"predictions data samples: {len(predictions)}")
        postprocessed_predictions = self.postprocess(predictions)
        logger.info(f"postprocessed_predictions data: {postprocessed_predictions}")
        logger.info(f"postprocessed_predictions data samples: {len(postprocessed_predictions)}")

        self._validate_all_instance_of(
            postprocessed_predictions, self.OUTPUT_SAMPLE_SCHEMA
        )

        return [sample.serialize() for sample in postprocessed_predictions]


    # def handle(self, data: List[Dict], context: Context) -> List[Dict[str, str]]:
    #     """
    #     Invoke by TorchServe for prediction request.
    #     Do pre-processing of data, prediction using model and postprocessing of
    #     prediction output.
    #
    #     :param data: Input data for prediction
    #     :param context: Initial context contains model server system properties.
    #     :return: prediction output
    #     """
    #     if len(data) == 0:
    #         return []
    #
    #     preprocessed_data_1 = self.preprocess(data)
    #     logger.info(f"preprocessed_data 1 {preprocessed_data_1}")
    #
    #     self._validate_all_instance_of(preprocessed_data_1, self.INPUT_SAMPLE_SCHEMA)
    #
    #     predictions_1 = self.inference(preprocessed_data_1)
    #     logger.info(f"predictions 1 {predictions_1}")
    #     postprocessed_predictions_1 = self.postprocess(predictions_1)
    #     logger.info(f"postprocessed_predictions 1 {postprocessed_predictions_1}")
    #
    #     self._validate_all_instance_of(
    #         postprocessed_predictions_1, self.OUTPUT_SAMPLE_SCHEMA
    #     )
    #
    #     preprocessed_data = self.preprocess(data)
    #     logger.info(f"preprocessed_data 2 {preprocessed_data}")
    #
    #     self._validate_all_instance_of(preprocessed_data, self.INPUT_SAMPLE_SCHEMA)
    #
    #     predictions = self.inference(preprocessed_data)
    #     logger.info(f"predictions 2 {predictions}")
    #     postprocessed_predictions = self.postprocess(predictions)
    #     logger.info(f"postprocessed_predictions 2 {postprocessed_predictions}")
    #
    #     self._validate_all_instance_of(
    #         postprocessed_predictions, self.OUTPUT_SAMPLE_SCHEMA
    #     )
    #
    #     # return [sample.serialize() for sample in postprocessed_predictions]
    #
    #     return [sample.serialize() for sample in postprocessed_predictions_1]
