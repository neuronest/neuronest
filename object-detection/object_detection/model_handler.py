import logging
from typing import Any, List, Optional, Tuple

import pandas as pd
from core.packages.abstract.online_prediction_model.model_handler import (
    OnlinePredictionModelHandler,
)
from core.schemas.object_detection import (
    InputSchemaSample as ObjectDetectionInputSchemaSample,
)
from core.schemas.object_detection import OutputSchemaSample
from core.serialization.array import array_to_string
from core.serialization.image import image_from_string
from imutils import resize

from object_detection.config import cfg

from object_detection.modules.model import ObjectDetectionModel  # isort:skip

# a relative import should be done here as this module is intended to be used with
# torchserve
# pylint: disable=import-error
# from config import cfg  # isort:skip
# from object_detection.model import ObjectDetectionModel  # isort:skip


# pylint: enable=import-error

logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)


class ObjectDetectionModelHandler(OnlinePredictionModelHandler):
    def __init__(
        self,
        *args,
        inner_model_type: Optional[str] = None,
        inner_model_name: Optional[str] = None,
        inner_model_tag: Optional[str] = None,
        image_width: Optional[int] = None,
        **kwargs,
        # device: Device = Device.CUDA,
    ):
        super().__init__(*args, **kwargs)
        # self.device = device.value
        # if device == Device.CUDA and not torch.cuda.is_available():
        #     logger.warning(f"GPU not detected while the asked device is {device.value}")
        #     self.device = Device.CPU.value
        # else:
        #     self.device = device.value

        # used with torchserve, torchserve has no way of knowing what values to pass
        # for these arguments, so it does not pass anything and in this case we source
        # ourselves explicitly in the config
        self.inner_model_tag = inner_model_tag or cfg.model.inner_model_tag
        self.inner_model_type = inner_model_type or cfg.model.inner_model_type
        self.inner_model_name = inner_model_name or cfg.model.inner_model_name
        self.image_width = image_width or cfg.model.image_width
        # self._context = None
        # self.initialized = False
        # self.model: Optional[OnlinePredictionModel] = None
        self.labels_to_predict: Optional[List[str]] = None
        self.confidence_threshold: Optional[float] = None

    # def _retrieve_model_path(self) -> str:
    #     properties = self._context.system_properties
    #     manifest = self._context.manifest
    #
    #     model_dir = properties.get("model_dir")
    #     serialized_file = manifest["model"]["serializedFile"]
    #
    #     return os.path.join(model_dir, serialized_file)
    @staticmethod
    def get_input_schema_sample_class():
        return ObjectDetectionInputSchemaSample

    def _fill_labels_to_predict(self, labels_to_predict: Optional[List[str]]):
        self.labels_to_predict = labels_to_predict

    def _fill_confidence_threshold(self, confidence_threshold: Optional[float]):
        self.confidence_threshold = confidence_threshold

    def _fill_image_width(self, overridden_image_width: Optional[int]):
        if overridden_image_width is not None:
            self.image_width = overridden_image_width

    def get_inference_data_and_other_args_kwargs_from_input_schema_samples(
        self, input_schema_samples: List[ObjectDetectionInputSchemaSample]
    ) -> Tuple[Tuple, dict]:
        # input_schema_samples = input_schema_samples.samples

        first_sample = input_schema_samples[0]

        self._fill_labels_to_predict(first_sample.labels_to_predict)
        self._fill_confidence_threshold(first_sample.confidence_threshold)
        self._fill_image_width(first_sample.overridden_image_width)

        return (
            (
                [
                    resize(image_from_string(sample.data), width=self.image_width)
                    for sample in input_schema_samples
                ],
            ),
            {},
        )

    # def preprocess(self, data: List[Dict[str, str]]) -> List[Any]:
    #
    #     validated_data_samples = super().preprocess(data=data)
    #
    #     first_sample = validated_data_samples[0]
    #
    #     self._fill_labels_to_predict(first_sample.labels_to_predict)
    #     self._fill_confidence_threshold(first_sample.confidence_threshold)
    #     self._fill_image_width(first_sample.overridden_image_width)
    #
    #     return [
    #         resize(image_from_string(sample.data), width=self.image_width)
    #         for sample in validated_data_samples
    #     ]

    # def inference(self, data: List[np.ndarray], *args, **kwargs) -> List[Any]:
    #     with torch.no_grad():
    #         self.model.eval()
    #         results = self.model(data, *args, **kwargs)
    #
    #     return results

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

    def postprocess(
        self, predictions: List[Any]
    ) -> List[OutputSchemaSample]:  # -> List[Dict[str, str]]:
        filtered_predictions = self._filter_predictions(predictions)

        return [
            OutputSchemaSample(results=array_to_string(prediction.values))
            for prediction in filtered_predictions
        ]

    # def initialize_model_pt(self, context: Context):
    #     self._context = context
    #
    #     model_pt_path = self._retrieve_model_path()
    #
    #     if not os.path.isfile(model_pt_path):
    #         raise RuntimeError("The model.pt file is missing")
    #
    #     # if self.device == Device.CUDA and not torch.cuda.is_available():
    #     #     logger.warning(f"GPU not detected while the device is {self.device}")
    #     #     self.device = Device.CPU.value
    #
    #     # self.model = ObjectDetectionModel(
    #     #     model_type=self.inner_model_type, model_name=self.inner_model_name
    #     # ).load(model_pt_path)
    #     model_pt = OnlinePredictionModel.get_model_pt_from_path(
    #         model_pt_path=model_pt_path
    #     )
    #     # self.model = OnlinePredictionModel.
    #     # self.model.to(self.device)
    #     model_pt.to(self.device)
    #     return model_pt

    # self.initialized = True

    def initialize_new_model(self):
        return ObjectDetectionModel(
            model_type=self.inner_model_type,
            model_name=self.inner_model_name,
            model_tag=self.inner_model_tag,
        )

    # def initialize(self, context: Context):
    #     """
    #     Initialize model. This will be called during model loading time
    #     :param context: Initial context contains model server system properties.
    #     :return:
    #     """
    #     model_pt = self.initialize_model_pt(context=context)
    #     self.model = ObjectDetectionModel(
    #         model_type=self.inner_model_type, model_name=self.inner_model_name
    #     )
    #     self.model.set_model(model=model_pt)

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

    # def handle(
    #     self, data: List[Dict[str, str]], context: Context
    # ) -> List[Dict[str, str]]:
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
    #     preprocessed_data = self.preprocess(data)
    #     predictions = self.inference(preprocessed_data)
    #     post_processed_predictions = self.postprocess(predictions)
    #
    #     if any(
    #         not isinstance(output, OutputSchema)
    #         for output in post_processed_predictions
    #     ):
    #         raise ValueError(
    #             f"Each output must be of type {OutputSchema.__name__} "
    #             f"or inherit from type {OutputSchema.__name__}"
    #         )
    #
    #     return [output.dict() for output in post_processed_predictions]
