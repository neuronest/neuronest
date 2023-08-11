import logging
import os
import uuid
from typing import List, Optional, Tuple, Union

from core.google.storage_client import StorageClient
from core.packages.abstract.online_prediction_model.model_handler import (
    OnlinePredictionModelHandler,
)
from core.schemas.video_comparator import (
    InputSchemaSample as VideoComparatorInputSchemaSample,
)
from core.schemas.video_comparator import OutputSchema as VideoComparatorOutputSchema

from video_comparator.config import cfg
from video_comparator.modules.model import VideoComparatorModel

# a relative import should be done here as this module is intended to be used with
# torchserve
# pylint: disable=import-error
# from config import cfg  # isort:skip
# from object_detection.model import ObjectDetectionModel  # isort:skip


# pylint: enable=import-error

logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)


class VideoComparatorModelHandler(OnlinePredictionModelHandler):
    def __init__(
        self,
        *args,
        # inner_model_type: Optional[str] = None,
        # inner_model_name: Optional[str] = None,
        # inner_model_tag: Optional[str] = None,
        # image_width: Optional[int] = None,
        batch_size: Optional[int] = None,
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
        self.batch_size = batch_size or cfg.model.batch_size
        # self.inner_model_tag = inner_model_tag or cfg.model.inner_model_tag
        # self.inner_model_type = inner_model_type or cfg.model.inner_model_type
        # self.inner_model_name = inner_model_name or cfg.model.inner_model_name
        # self.image_width = image_width or cfg.model.image_width
        # self._context = None
        # self.initialized = False
        # self.model: Optional[OnlinePredictionModel] = None
        # self.labels_to_predict: Optional[List[str]] = None
        # self.confidence_threshold: Optional[float] = None
        self.storage_client = StorageClient()

    # def _retrieve_model_path(self) -> str:
    #     properties = self._context.system_properties
    #     manifest = self._context.manifest
    #
    #     model_dir = properties.get("model_dir")
    #     serialized_file = manifest["model"]["serializedFile"]
    #
    #     return os.path.join(model_dir, serialized_file)

    # def _fill_labels_to_predict(self, labels_to_predict: Optional[List[str]]):
    #     self.labels_to_predict = labels_to_predict
    #
    # def _fill_confidence_threshold(self, confidence_threshold: Optional[float]):
    #     self.confidence_threshold = confidence_threshold
    #
    # def _fill_image_width(self, overridden_image_width: Optional[int]):
    #     if overridden_image_width is not None:
    #         self.image_width = overridden_image_width

    @staticmethod
    def get_input_schema_sample_class():
        return VideoComparatorInputSchemaSample

    def get_inference_data_and_other_args_kwargs_from_input_schema_samples(
        self, input_schema_samples: List[VideoComparatorInputSchemaSample]
    ) -> Tuple[Tuple, dict]:
        sample = input_schema_samples[0]
        video_path = (
            f"{str(uuid.uuid4())}{sample.video_path.get_file_extension() or ''}"
        )
        self.storage_client.download_blob_to_file(
            bucket_name=sample.video_path.bucket,
            source_blob_name=sample.video_path.blob_name,
            destination_file_name=video_path,
        )
        if sample.other_video_path is not None:
            other_video_path = (
                f"{str(uuid.uuid4())}"
                f"{sample.other_video_path.get_file_extension() or ''}"
            )
            self.storage_client.download_blob_to_file(
                bucket_name=sample.other_video_path.bucket,
                source_blob_name=sample.other_video_path.blob_name,
                destination_file_name=other_video_path,
            )
        else:
            other_video_path = None
        return (
            (),
            {
                "prediction_type": input_schema_samples[0].prediction_type,
                "video_path": video_path,
                "other_video_path": other_video_path,
                "batch_size": self.batch_size,
                "delete_videos_after_inference": True,
            },
        )

    # pylint: disable=arguments-differ
    def inference(
        self,
        video_path: str,
        other_video_path: str,
        prediction_type: str,
        batch_size: int = 128,
        delete_videos_after_inference: bool = True,
    ) -> list:
        prediction = super().inference(
            video_path=video_path,
            other_video_path=other_video_path,
            prediction_type=prediction_type,
            batch_size=batch_size,
        )
        if delete_videos_after_inference:
            os.remove(video_path)
            os.remove(other_video_path)
        return [prediction]

    # @implements_abstract_method(OnlinePredictionModelHandler.preprocess)
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

    def postprocess(
        self, predictions: Union[List[float], List[float]]
    ) -> VideoComparatorOutputSchema:  # -> List[Dict[str, str]]:
        return VideoComparatorOutputSchema(results=predictions)

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
        return VideoComparatorModel()

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
