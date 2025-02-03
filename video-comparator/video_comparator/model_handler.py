import logging
from typing import Any, Dict, List, Optional, Tuple

import torch
from core.google.storage_client import StorageClient
from core.packages.abstract.online_prediction_model.model_handler import (
    OnlinePredictionModelHandler,
)
from core.schemas.abstract.online_prediction_model import Device
from core.schemas.asset import AssetType
from core.schemas.modules.video_comparator import (
    InputSampleSchema as VideoComparatorInputSampleSchema,
)
from core.schemas.modules.video_comparator import (
    OutputSampleSchema as VideoComparatorOutputSampleSchema,
)
from core.services.asset_reader import make_asset

from video_comparator.config import cfg
from video_comparator.modules.model import VideoComparatorModel
from video_comparator.modules.schemas import ModelInput

logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)


class VideoComparatorModelHandler(OnlinePredictionModelHandler):
    INPUT_SAMPLE_SCHEMA = VideoComparatorInputSampleSchema
    OUTPUT_SAMPLE_SCHEMA = VideoComparatorOutputSampleSchema

    def __init__(
        self,
        *args,
        storage_client: Optional[StorageClient] = None,
        batch_size: Optional[int] = None,
        center_crop_size: Optional[int] = None,
        device: Device = Device.CUDA,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.storage_client = storage_client or StorageClient()
        self.batch_size = batch_size or cfg.model.batch_size
        self.center_crop_size = center_crop_size or cfg.preprocessing.center_crop_size
        self.device = device

    def create_new_model(self):
        return VideoComparatorModel()

    def inference(
        self, data: List[VideoComparatorInputSampleSchema], *args, **kwargs
    ) -> List[Any]:
        if len(data) == 0:
            return []

        predictions = []

        for sample in data:
            video_asset, other_video_asset = None, None

            if sample.video_path is not None:
                video_asset = make_asset(
                    asset_path=sample.video_path,
                    asset_type=AssetType.VIDEO,
                    storage_client=self.storage_client,
                    time_step=1 / cfg.preprocessing.fps,
                    resized_shape_or_minimal_value=cfg.preprocessing.image_size,
                )

            if sample.other_video_path is not None:
                other_video_asset = make_asset(
                    asset_path=sample.other_video_path,
                    asset_type=AssetType.VIDEO,
                    storage_client=self.storage_client,
                    time_step=1 / cfg.preprocessing.fps,
                    resized_shape_or_minimal_value=cfg.preprocessing.image_size,
                )

            predictions.append(
                super().inference(
                    data=[
                        ModelInput(
                            video=(
                                torch.from_numpy(video_asset.as_array_content)
                                if video_asset is not None
                                else None
                            ),
                            other_video=(
                                torch.from_numpy(other_video_asset.as_array_content)
                                if other_video_asset is not None
                                else None
                            ),
                            video_embedding=(
                                torch.from_numpy(sample.video_embedding)
                                if sample.video_embedding is not None
                                else None
                            ),
                            other_video_embedding=(
                                torch.from_numpy(sample.other_video_embedding)
                                if sample.other_video_embedding is not None
                                else None
                            ),
                        )
                    ],
                    device=self.device,
                    batch_size=self.batch_size,
                    center_crop_size=self.center_crop_size,
                )
            )

        return predictions

    def postprocess(
        self, data: List[Tuple[torch.Tensor, torch.Tensor, torch.Tensor]]
    ) -> List[VideoComparatorOutputSampleSchema]:
        postprocessed_predictions = []

        for sample in data:
            video_embedding, other_video_embedding, similarity_score = sample

            postprocessed_predictions.append(
                VideoComparatorOutputSampleSchema(
                    video_embedding=video_embedding.numpy(),
                    other_video_embedding=other_video_embedding.numpy(),
                    similarity_score=similarity_score.item(),
                )
            )

        return postprocessed_predictions

    def handle(self, data: List[Dict], context) -> List[Dict[str, str]]:
        if len(data) > 1:
            logger.info(
                "The model does not currently manage batched predictions, i.e. "
                "more than one pair of videos, partly because a single pair "
                "monopolizes the GPU and takes a long time to process. Instead, only "
                "one sample will be processed at a time; there will be no batched "
                "inference."
            )

        return super().handle(data=data, context=context)
