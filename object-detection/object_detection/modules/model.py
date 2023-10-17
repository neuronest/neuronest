from __future__ import annotations

from typing import List

import pandas as pd
import torch
from core.packages.abstract.online_prediction_model.modules.model import (
    OnlinePredictionModel,
)


class ObjectDetectionModel(OnlinePredictionModel):
    def __init__(
        self,
        model_type: str,
        model_name: str,
        *args,
        **kwargs,
    ):
        self.model_type = model_type
        self.model_name = model_name
        super().__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs) -> List[pd.DataFrame]:
        # noinspection PyCallingNonCallable
        predictions = self._model(*args, **kwargs)

        return list(predictions.pandas().xyxy)

    def _retrieve_remote_model(self, pretrained: bool = False):
        return torch.hub.load(self.model_type, self.model_name, pretrained=pretrained)

    def fit(self, *args, **kwargs):
        # pylint: disable=attribute-defined-outside-init
        self._model = self._retrieve_remote_model(pretrained=True)

    def load(self, path: str) -> ObjectDetectionModel:
        # loads in memory the project architecture of the model so that it is visible
        # to the interpreter when loading the MODEL.pt
        self._retrieve_remote_model(pretrained=False)
        self._model = torch.load(path)
        return self
