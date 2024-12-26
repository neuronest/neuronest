from __future__ import annotations

from typing import List, Tuple, Union

import numpy as np
import torch
from core.packages.abstract.online_prediction_model.modules.model import (
    OnlinePredictionModel,
)
from core.schemas.abstract.online_prediction_model import Device

from video_comparator.model.visil import ViSiL
from video_comparator.modules.schemas import ModelInput


class VideoComparatorModel(OnlinePredictionModel):
    def __init__(self):
        super().__init__()

    # pylint: disable=arguments-differ
    def __call__(
        self,
        model_input: ModelInput,
        device: Device,
        batch_size: int,
        center_crop_size: int,
    ) -> List[Tuple[torch.Tensor, torch.Tensor, torch.Tensor]]:
        video_embedding = (
            model_input.video_embedding.to(device)
            if model_input.video_embedding is not None
            else self._extract_features(
                model=self._model,
                frames=self._center_crop(
                    frames=model_input.video,
                    desired_size=center_crop_size,
                ),
                device=device,
                batch_sz=batch_size,
            )
        )

        other_video_embedding = (
            model_input.other_video_embedding.to(device)
            if model_input.other_video_embedding is not None
            else self._extract_features(
                model=self._model,
                frames=self._center_crop(
                    frames=model_input.other_video,
                    desired_size=center_crop_size,
                ),
                device=device,
                batch_sz=batch_size,
            )
        )

        return [
            (
                video_embedding.to(Device.CPU),
                other_video_embedding.to(Device.CPU),
                self._model.calculate_video_similarity(
                    query=video_embedding,
                    target=other_video_embedding,
                ).to(Device.CPU),
            )
        ]

    @staticmethod
    @torch.no_grad()
    def _center_crop(frames: torch.Tensor, desired_size: int) -> torch.Tensor:
        if frames.ndim == 3:
            old_size = frames.shape[:2]
            top = int(np.maximum(0, (old_size[0] - desired_size) / 2))
            left = int(np.maximum(0, (old_size[1] - desired_size) / 2))

            return frames[top : top + desired_size, left : left + desired_size, :]

        old_size = frames.shape[1:3]
        top = int(np.maximum(0, (old_size[0] - desired_size) / 2))
        left = int(np.maximum(0, (old_size[1] - desired_size) / 2))

        return frames[:, top : top + desired_size, left : left + desired_size, :]

    @staticmethod
    @torch.no_grad()
    def _extract_features(
        model: ViSiL,
        frames: torch.Tensor,
        batch_sz: int,
        device: Union[int, str] = None,
    ):
        features = []
        for i in range(frames.shape[0] // batch_sz + 1):
            batch = frames[i * batch_sz : (i + 1) * batch_sz]
            if batch.shape[0] > 0:
                if device is not None:
                    batch = batch.to(device).float()
                features.append(model.extract_features(batch))
        features = torch.cat(features, 0)
        while features.shape[0] < 4:
            features = torch.cat([features, features], 0)

        return features

    def retrieve_remote_model(self, pretrained: bool = False) -> ViSiL:
        visil = ViSiL(pretrained=pretrained)
        visil.eval()

        return visil

    def fit(self, *args, **kwargs):
        self._model = self.retrieve_remote_model(pretrained=True)
