import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
from core.google.storage_client import StorageClient
from core.packages.abstract.online_prediction_model.model_handler import (
    OnlinePredictionModelHandler,
)
from core.path import GSPath
from core.schemas.abstract.online_prediction_model import Device
from core.schemas.asset import AssetType, VideoAsset
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
from video_comparator.services.embedding_manager import EmbeddingManager

logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)


class VideoComparatorModelHandler(OnlinePredictionModelHandler):
    INPUT_SAMPLE_SCHEMA = VideoComparatorInputSampleSchema
    OUTPUT_SAMPLE_SCHEMA = VideoComparatorOutputSampleSchema

    def __init__(
        self,
        *args,
        storage_client: Optional[StorageClient] = None,
        embedding_manager: Optional[EmbeddingManager] = None,
        batch_size: Optional[int] = None,
        center_crop_size: Optional[int] = None,
        device: Device = Device.CUDA,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.storage_client = storage_client or StorageClient()
        self.embedding_manager = embedding_manager or EmbeddingManager(
            storage_client=self.storage_client
        )
        self.batch_size = batch_size or cfg.model.batch_size
        self.center_crop_size = center_crop_size or cfg.preprocessing.center_crop_size
        self.device = device

    def _init_asset(
        self, video_path: GSPath, embedding_bucket_name: str
    ) -> Tuple[VideoAsset, str, Optional[np.ndarray]]:
        video_asset = make_asset(
            asset_path=video_path,
            asset_type=AssetType.VIDEO,
            storage_client=self.storage_client,
            time_step=1 / cfg.preprocessing.fps,
            resized_shape_or_minimal_value=cfg.preprocessing.image_size,
        )
        video_asset_id = video_asset.get_hash()
        video_asset_existing_embedding = self.embedding_manager.retrieve_embedding(
            bucket_name=embedding_bucket_name,
            asset_id=video_asset_id,
            is_missing_ok=True,
        )

        return video_asset, video_asset_id, video_asset_existing_embedding

    def create_new_model(self):
        return VideoComparatorModel()

    def inference(
        self, data: List[VideoComparatorInputSampleSchema], *args, **kwargs
    ) -> List[Any]:
        if len(data) == 0:
            return []

        predictions = []

        for sample in data:
            video_asset, video_asset_id, video_asset_existing_embedding = (
                self._init_asset(sample.video_path, sample.embedding_bucket_name)
            )
            (
                other_video_asset,
                other_video_asset_id,
                other_video_asset_existing_embedding,
            ) = self._init_asset(sample.other_video_path, sample.embedding_bucket_name)

            prediction = super().inference(
                data=[
                    ModelInput(
                        video=(
                            torch.from_numpy(video_asset.as_array_content)
                            if video_asset_existing_embedding is None
                            else None
                        ),
                        other_video=(
                            torch.from_numpy(other_video_asset.as_array_content)
                            if other_video_asset_existing_embedding is None
                            else None
                        ),
                        video_embedding=(
                            torch.from_numpy(video_asset_existing_embedding)
                            if video_asset_existing_embedding is not None
                            else None
                        ),
                        other_video_embedding=(
                            torch.from_numpy(other_video_asset_existing_embedding)
                            if other_video_asset_existing_embedding is not None
                            else None
                        ),
                    )
                ],
                device=self.device,
                batch_size=self.batch_size,
                center_crop_size=self.center_crop_size,
            )

            video_embedding, other_video_embedding, similarity_score = prediction[0]

            self.embedding_manager.store_multiple_embeddings(
                bucket_name=sample.embedding_bucket_name,
                asset_ids=[video_asset_id, other_video_asset_id],
                embeddings=[
                    video_embedding,
                    other_video_embedding,
                ],
            )

            predictions.append(similarity_score)

        return predictions

    def postprocess(
        self, data: List[torch.Tensor]
    ) -> List[VideoComparatorOutputSampleSchema]:
        postprocessed_predictions = []

        for sample in data:
            similarity_score = sample

            postprocessed_predictions.append(
                VideoComparatorOutputSampleSchema(
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
