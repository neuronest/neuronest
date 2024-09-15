import logging
from typing import Any, Dict, List, Optional, Tuple

import torch
from core.packages.abstract.online_prediction_model.model_handler import (
    OnlinePredictionModelHandler,
)
from core.schemas.abstract.online_prediction_model import Device
from core.schemas.video_comparator import (
    InputSampleSchema as VideoComparatorInputSampleSchema,
)
from core.schemas.video_comparator import (
    OutputSampleSchema as VideoComparatorOutputSampleSchema,
)

from video_comparator.config import cfg
from video_comparator.modules.model import VideoComparatorModel

logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)


class VideoComparatorModelHandler(OnlinePredictionModelHandler):
    INPUT_SAMPLE_SCHEMA = VideoComparatorInputSampleSchema
    OUTPUT_SAMPLE_SCHEMA = VideoComparatorOutputSampleSchema

    def __init__(
        self,
        *args,
        batch_size: Optional[int] = None,
        image_size: Optional[int] = None,
        center_crop_size: Optional[int] = None,
        fps: Optional[int] = None,
        device: Device = Device.CUDA,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.batch_size = batch_size or cfg.model.batch_size
        self.image_size = image_size or cfg.preprocessing.image_size
        self.center_crop_size = center_crop_size or cfg.preprocessing.center_crop_size
        self.fps = fps or cfg.preprocessing.fps
        self.device = device

    def create_new_model(self):
        return VideoComparatorModel()

    def inference(
        self, data: List[VideoComparatorInputSampleSchema], **kwargs
    ) -> List[Any]:
        sample = data[0]  # expected to be only one sample

        return super().inference(
            sample=sample,
            device=self.device,
            batch_size=self.batch_size,
            fps=self.fps,
            image_size=self.image_size,
            center_crop_size=self.center_crop_size,
        )

    def postprocess(
        self, data: List[Tuple[torch.Tensor, torch.Tensor, torch.Tensor]]
    ) -> List[VideoComparatorOutputSampleSchema]:
        sample = data[0]  # expected to be only one sample

        video_embedding, other_video_embedding, similarity_results = sample

        return [
            VideoComparatorOutputSampleSchema(
                video_embedding=video_embedding.numpy(),
                other_video_embedding=other_video_embedding.numpy(),
                similarity_results=similarity_results.item(),
            )
        ]

    def handle(self, data: List[Dict], context) -> List[Dict[str, str]]:
        if len(data) > 1:
            raise ValueError(
                "The model does not currently manage batched predictions, i.e. "
                "more than one pair of videos, partly because a single pair "
                "monopolizes the GPU and takes a long time to process"
            )

        return super().handle(data=data, context=context)
