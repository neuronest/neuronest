from __future__ import annotations

from typing import List

import pandas as pd
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

    def retrieve_remote_model(self, pretrained: bool = False):
        return self._load_hub_model(
            model_type=self.model_type,
            model_name=self.model_name,
            pretrained=pretrained,
        )

    def fit(self, *args, **kwargs):
        # pylint: disable=attribute-defined-outside-init
        self._model = self.retrieve_remote_model(pretrained=True)
