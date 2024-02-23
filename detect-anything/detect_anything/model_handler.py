import logging
from typing import Any, Dict, List, Tuple, Type

from core.packages.abstract.online_prediction_model.model_handler import (
    OnlinePredictionModelHandler,
)
from core.schemas.detect_anything import DetectAnythingImagePredictions
from core.schemas.detect_anything import (
    InputSampleSchema as DetectAnythingInputSampleSchema,
)
from core.schemas.detect_anything import (
    OutputSampleSchema as DetectAnythingOutputSampleSchema,
)
from core.schemas.video_comparator import (
    InputSampleSchema as VideoComparatorInputSampleSchema,
)
from detect_anything.modules.model import DetectAnythingModel

logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)


class DetectAnythingModelHandler(OnlinePredictionModelHandler):
    def __init__(
        self,
        *args,
        # batch_size: Optional[int] = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        # self.batch_size = batch_size or cfg.model.batch_size
        # self.storage_client = StorageClient()

    # def _preprocess_video(self, video: Union[GSPath, np.ndarray]):
    #     if isinstance(video, GSPath):
    #         video_path = str(uuid.uuid4())
    #         self.storage_client.download_blob_to_file(
    #             bucket_name=video.bucket,
    #             source_blob_name=video.blob_name,
    #             destination_file_name=video_path,
    #         )
    #         return video_path
    #     if isinstance(video, np.ndarray):
    #         return video
    #     raise ValueError

    def create_new_model(self):
        return DetectAnythingModel()

    # def _get_input_sample_schema_from_data_sample(self, data_sample: dict):
    #     raise VideoComparatorInputSampleSchema.parse_obj(data_sample)

    def _get_input_sample_schema_class(self) -> Type[VideoComparatorInputSampleSchema]:
        return DetectAnythingInputSampleSchema

    def build_inference_args_kwargs_from_input_samples_schema(
        self, input_samples_schema: List[DetectAnythingInputSampleSchema]
    ) -> List[Tuple[Tuple[Any], Dict[str, Any]]]:
        return [
            (
                (),
                {
                    "rgb_image": input_sample_schema.rgb_image,
                    "texts_prompt": input_sample_schema.texts_prompt,
                    "box_threshold": input_sample_schema.box_threshold,
                    "text_threshold": input_sample_schema.text_threshold,
                    "annotate_image": input_sample_schema.annotate_image,
                    "device": "cuda",
                },
            )
            for input_sample_schema in input_samples_schema
        ]

    # pylint: disable=arguments-differ
    # def inference(
    #     self,
    #     # video: Union[str, np.ndarray],
    #     # other_video: Optional[Union[str, np.ndarray]],
    #     video_other_video_pairs: List[
    #         Tuple[Union[str, np.ndarray], Optional[Union[str, np.ndarray]]]
    #     ],
    #     prediction_type: str,
    #     batch_size: int = 128,
    #     delete_videos_after_inference: bool = True,
    # ) -> list:
    #     predictions = []
    #     for video, other_video in video_other_video_pairs:
    #         predictions.append(
    #             super().inference(
    #                 video=video,
    #                 other_video=other_video,
    #                 prediction_type=prediction_type,
    #                 batch_size=batch_size,
    #             )
    #         )
    #         if isinstance(video, str) and delete_videos_after_inference:
    #             os.remove(video)
    #         if isinstance(other_video, str) and delete_videos_after_inference:
    #             os.remove(other_video)
    #
    #     return predictions

    # pylint: disable=arguments-renamed
    def postprocess(
        self, predictions: List[DetectAnythingImagePredictions]
    ) -> List[DetectAnythingOutputSampleSchema]:
        return [
            DetectAnythingOutputSampleSchema(results=prediction)
            for prediction in predictions
        ]

    def handle(self, data: List[Dict], context) -> List[Dict[str, str]]:
        if len(data) > 1:
            raise ValueError(
                "The model does not currently manage batched predictions, i.e. "
                "more than one pair of videos, partly because a single pair "
                "monopolizes the GPU and takes a long time to process"
            )

        return super().handle(data=data, context=context)
        # return [
        #     {
        #         key: array_to_string(value) if isinstance(value, np.ndarray) else value
        #         for key, value in prediction.items()
        #     }
        #     for prediction in predictions
        # ]
