from typing import Dict, List

import numpy as np
import pandas as pd
from imutils import resize

from core.client.abstract.online_prediction_model import OnlinePredictionModelClient
from core.schemas.object_detection import PREDICTION_COLUMNS, OutputSchemaSample
from core.serialization.array import array_from_string
from core.serialization.image import image_to_string


class ObjectDetectionClient(OnlinePredictionModelClient):
    PREPROCESSING_IMAGE_TYPE = ".jpg"
    MAX_SIZE = (640, 640)
    MAX_BYTES = 1.5e6

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

    def _split_into_chunks(
        self, preprocessed_images: List[Dict[str, str]]
    ) -> List[List[Dict[str, str]]]:
        if len(preprocessed_images) == 0:
            return []

        if len(preprocessed_images) == 1:
            return [preprocessed_images]

        if (
            sum(
                len(preprocessed_image["data"])
                for preprocessed_image in preprocessed_images
            )
            <= self.MAX_BYTES
        ):
            return [preprocessed_images]

        for index, preprocessed_image in enumerate(preprocessed_images):
            if (image_bytes := len(preprocessed_image["data"])) > self.MAX_BYTES:
                raise ValueError(
                    f"Cannot proceed, image at index {index} is too large: "
                    f"{image_bytes/1e6}MB"
                )

        chunks, bytes_current_chunk = [[preprocessed_images[0]]], len(
            preprocessed_images[0]["data"]
        )
        for preprocessed_image in preprocessed_images[1:]:
            bytes_current_image = len(preprocessed_image["data"])
            if bytes_current_image + bytes_current_chunk <= self.MAX_BYTES:
                chunks[-1].append(preprocessed_image)
                bytes_current_chunk += bytes_current_image
                continue

            chunks.append([preprocessed_image])
            bytes_current_chunk = bytes_current_image

        return chunks

    # pylint: disable=arguments-renamed
    def predict_batch(self, images: List[np.ndarray]) -> List[pd.DataFrame]:
        """
        images: List of RGB images as NumPy arrays
        """
        if not self._are_shapes_correct(images):
            raise ValueError("Incorrect received shapes")

        preprocessed_images = [
            {
                "data": image_to_string(
                    frame=image,
                    extension=self.PREPROCESSING_IMAGE_TYPE,
                )
            }
            for image in self._resize_images(images=images)
        ]
        chunks_preprocessed_images = self._split_into_chunks(preprocessed_images)

        endpoint = self._try_get_endpoint()
        raw_chunked_predictions = [
            endpoint.predict(chunk_preprocessed_images).predictions
            for chunk_preprocessed_images in chunks_preprocessed_images
        ]
        predictions = [
            array_from_string(OutputSchemaSample.parse_obj(raw_prediction).results)
            for raw_predictions in raw_chunked_predictions
            for raw_prediction in raw_predictions
        ]

        return [
            pd.DataFrame(prediction, columns=PREDICTION_COLUMNS)
            for prediction in predictions
        ]
