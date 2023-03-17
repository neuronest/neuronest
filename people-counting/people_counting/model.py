from typing import List

import numpy as np
from core.client.object_detection import ObjectDetectionClient

from people_counting.common import BoundingBox


# pylint: disable=too-few-public-methods
class Model:
    def __init__(
        self,
        object_detection_client: ObjectDetectionClient,
        confidence_threshold: float,
    ):
        self.object_detection_client = object_detection_client
        self.confidence_threshold = confidence_threshold

    def predict(
        self,
        image: np.ndarray,
        class_name: str = "person",
    ) -> List[BoundingBox]:
        results = self.object_detection_client.predict_single(image)
        filtered_results = results[
            (results.score >= self.confidence_threshold)
            & (results.class_name == class_name)
        ]
        return [
            BoundingBox(
                x_min=int(row.x_min),
                y_min=int(row.y_min),
                x_max=int(row.x_max),
                y_max=int(row.y_max),
            )
            for row in filtered_results.itertuples()
        ]
