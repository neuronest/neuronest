from typing import List

import numpy as np
from core.client.object_detection import ObjectDetectionClient

from people_counting.common import BoundingBox


class Model:
    def __init__(
        self,
        object_detection_client: ObjectDetectionClient,
        confidence_threshold: float,
        class_name: str = "person",
    ):
        self.object_detection_client = object_detection_client
        self.confidence_threshold = confidence_threshold
        self.class_name = class_name

    def predict_batch(
        self,
        images: List[np.ndarray],
    ) -> List[List[BoundingBox]]:
        results_batch = self.object_detection_client.predict_batch(
            images,
            labels=[self.class_name],
            confidence_threshold=self.confidence_threshold,
        )

        return [
            results.apply(
                lambda row: BoundingBox(
                    x_min=int(row.x_min),
                    y_min=int(row.y_min),
                    x_max=int(row.x_max),
                    y_max=int(row.y_max),
                )
            ).tolist()
            for results in results_batch
        ]

    def predict(
        self,
        image: np.ndarray,
    ) -> List[BoundingBox]:
        return self.predict_batch(images=[image])[0]
