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
from video_comparator.utils import extract_features
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
            video_features = extract_features(
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
            other_video_features = extract_features(
                model=self._model,
                frames=torch.from_numpy(visil_video_load(other_video)),
                device=device,
                batch_sz=batch_size,
            )
        return self._model.calculate_video_similarity(
            query=video_features, target=other_video_features
        )

    def _retrieve_remote_model(self, pretrained: bool = False):
        visil = ViSiL(pretrained=pretrained)
        visil.eval()
        return visil

    def fit(self, *args, **kwargs):
        # pylint: disable=attribute-defined-outside-init
        self._model = self._retrieve_remote_model(pretrained=True)
