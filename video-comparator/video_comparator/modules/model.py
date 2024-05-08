from __future__ import annotations

from typing import Optional, Union

import numpy as np
import torch
from core.packages.abstract.online_prediction_model.modules.model import (
    OnlinePredictionModel,
)
from core.schemas.abstract.online_prediction_model import Device
from core.schemas.video_comparator import PredictionType

from video_comparator.model.visil import ViSiL
from video_comparator.utils import load_video as visil_video_load


class VideoComparatorModel(OnlinePredictionModel):
    def __init__(self):
        super().__init__()

    # pylint: disable=arguments-differ
    def __call__(
        self,
        video: Union[str, np.ndarray],
        other_video: Optional[Union[str, np.ndarray]] = None,
        prediction_type: str = PredictionType.SIMILARITY,
        device: Device = Device.CUDA,
        batch_size: int = 128,
    ) -> Union[torch.Tensor, float]:
        if isinstance(video, np.ndarray):
            video_features = torch.from_numpy(video).to(device)
        else:
            video_features = self._extract_features(
                model=self._model,
                frames=torch.from_numpy(visil_video_load(video)),
                device=device,
                batch_sz=batch_size,
            )
        if prediction_type == PredictionType.VIDEO_FEATURES:
            return video_features.cpu().numpy()
        if isinstance(other_video, np.ndarray):
            other_video_features = torch.from_numpy(other_video).to(device)
        else:
            other_video_features = self._extract_features(
                model=self._model,
                frames=torch.from_numpy(visil_video_load(other_video)),
                device=device,
                batch_sz=batch_size,
            )
        return self._model.calculate_video_similarity(
            query=video_features, target=other_video_features
        )

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

    def _retrieve_remote_model(self, pretrained: bool = False) -> ViSiL:
        visil = ViSiL(pretrained=pretrained)
        visil.eval()

        return visil

    def fit(self, *args, **kwargs):
        # pylint: disable=attribute-defined-outside-init
        self._model = self._retrieve_remote_model(pretrained=True)
