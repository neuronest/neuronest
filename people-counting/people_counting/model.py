from typing import List

import numpy as np
import torch

from people_counting.common import BoundingBox


# pylint: disable=too-few-public-methods
class ObjectDetectionModel:
    def __init__(self, model_type: str, model_name: str, confidence_threshold: float):
        self.model_type = model_type
        self.model_name = model_name
        self.confidence_threshold = confidence_threshold
        self.model: torch.nn.Module = self._load_hub_pretrained_model()

    def _load_hub_pretrained_model(self) -> torch.nn.Module:
        return torch.hub.load(self.model_type, self.model_name, pretrained=True)

    def predict(self, image: np.ndarray, class_name: str) -> List[BoundingBox]:
        results = self.model(image).pandas().xyxy[0]
        filtered_results = results[
            (results.confidence >= self.confidence_threshold)
            & (results.name == class_name)
        ]
        return [
            BoundingBox(
                x_min=int(row.xmin),
                y_min=int(row.ymin),
                x_max=int(row.xmax),
                y_max=int(row.ymax),
            )
            for row in filtered_results.itertuples()
        ]
