from typing import List, Optional

import numpy as np
import pandas as pd
from imutils import resize

from core.client.abstract.online_prediction_model import OnlinePredictionModelClient
from core.schemas.object_detection import (
    InputSampleSchema as ObjectDetectionInputSampleSchema,
)


class ObjectDetectionClient(OnlinePredictionModelClient):
    PREPROCESSING_IMAGE_TYPE = ".jpg"
    MAX_SIZE = (640, 640)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @staticmethod
    def _are_shapes_correct(images: List[np.ndarray]) -> bool:
        if any(
            image.ndim not in (2, 3) or image.ndim == 3 and image.shape[2] != 3
            for image in images
        ):
            return False

        return True

    def _resize_images(self, images: List[np.ndarray]) -> List[np.ndarray]:
        """
        If any dimension of an image if greater than self.MAX_SIZE (width, height),
        then the image is going to be resized without changing the ratio,
        with self.MAX_SIZE being the maximum.
        """
        return [
            resize(
                image=image,
                height=self.MAX_SIZE[0]
                if image.shape[0] > self.MAX_SIZE[0] and image.shape[0] > image.shape[1]
                else None,
                width=self.MAX_SIZE[1]
                if image.shape[1] > self.MAX_SIZE[1] and image.shape[1] > image.shape[0]
                else None,
            )
            for image in images
        ]

    # # pylint: disable=arguments-differ,arguments-renamed
    # def _batch_sample_to_input_sample_schema(
    #     self, image: np.ndarray
    # ) -> ObjectDetectionInputSampleSchema:
    #     return ObjectDetectionInputSampleSchema(image=image)

    # pylint: disable=arguments-differ,arguments-renamed
    def _batch_sample_to_input_sample_schema(
        self,
        batch_sample_image: np.ndarray,
        labels: Optional[List[str]] = None,
        confidence_threshold: Optional[float] = None,
    ) -> ObjectDetectionInputSampleSchema:
        resized_batch_sample_image = self._resize_images([batch_sample_image])[0]

        return ObjectDetectionInputSampleSchema(
            image=resized_batch_sample_image,
            labels_to_predict=labels,
            confidence_threshold=confidence_threshold,
        )

    # pylint: disable=arguments-differ,arguments-renamed
    def predict_batch(
        self,
        images: List[np.ndarray],
        labels: Optional[List[str]] = None,
        confidence_threshold: Optional[float] = None,
    ) -> List[pd.DataFrame]:
        """
        images: List of RGB images as NumPy arrays
        """
        if not self._are_shapes_correct(images):
            raise ValueError("Incorrect received shapes")

        return super().predict_batch(
            batch=images, labels=labels, confidence_threshold=confidence_threshold
        )
        # return [
        #     pd.DataFrame(prediction, columns=PREDICTION_COLUMNS)
        #     for prediction in super().predict_batch(
        #         batch=images, labels=labels, confidence_threshold=confidence_threshold
        #     )
        # ]
