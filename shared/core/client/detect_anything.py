import math
from functools import lru_cache
from typing import List, Tuple, Type, Union

import cv2 as cv
import numpy as np
import pandas as pd
from imutils import resize

from core.client.abstract.online_prediction_model import OnlinePredictionModelClient
from core.schemas.detect_anything import (
    InputSampleSchema as DetectAnythingInputSampleSchema,
)
from core.schemas.detect_anything import (
    OutputSampleSchema as DetectAnythingOutputSampleSchema,
)


@lru_cache
def get_new_height_width_preserve_ratio(
    old_height: int, old_width: int, pixels_amount: int
) -> Tuple[int, int]:
    height_over_width = old_height / old_width
    new_width = int(math.sqrt(pixels_amount / height_over_width))
    new_height = int(new_width * height_over_width)

    return new_height, new_width


class DetectAnythingClient(OnlinePredictionModelClient):
    MAX_PIXELS = 640 * 640

    def __init__(
        self,
        *online_prediction_model_client_args,
        **online_prediction_model_client_kwargs
    ):
        super().__init__(
            *online_prediction_model_client_args,
            **online_prediction_model_client_kwargs
        )

    @staticmethod
    def _are_shapes_correct(images: List[np.ndarray]) -> bool:
        if any(
            image.ndim not in (2, 3) or image.ndim == 3 and image.shape[2] != 3
            for image in images
        ):
            return False

        return True

    def _resize_image(self, image: np.ndarray) -> np.ndarray:
        if self.MAX_PIXELS:
            return image

        resized_image_height, resized_image_width = get_new_height_width_preserve_ratio(
            old_height=image.shape[0],
            old_width=image.shape[1],
            pixels_amount=self.MAX_PIXELS,
        )

        return resize(
            image=image,
            height=resized_image_height,
            width=resized_image_width,
        )

    def _resize_images(self, images: List[np.ndarray]) -> List[np.ndarray]:
        """
        If any dimension of an image if greater than self.MAX_SIZE (width, height),
        then the image is going to be resized without changing the ratio,
        with self.MAX_SIZE being the maximum.
        """
        return [self._resize_image(image=image) for image in images]

    def get_output_sample_schema_class(self) -> Type[DetectAnythingOutputSampleSchema]:
        return DetectAnythingOutputSampleSchema

    # pylint: disable=arguments-differ,arguments-renamed
    def _batch_sample_to_input_sample_schema(
        self,
        image_and_texts_prompts: Tuple[np.ndarray, str],
        box_threshold: float = 0.35,
        text_threshold: float = 0.25,
    ) -> DetectAnythingInputSampleSchema:
        resized_batch_sample_image = self._resize_images([image_and_texts_prompts[0]])[
            0
        ]

        return DetectAnythingInputSampleSchema(
            rgb_image=resized_batch_sample_image,
            texts_prompt=image_and_texts_prompts[1],
            box_threshold=box_threshold,
            text_threshold=text_threshold,
        )

    def _load_image(self, image: Union[str, np.ndarray]) -> np.ndarray:
        """
        Loads an image into a numpy array.

        :param image_path: Either a path to an image or a numpy array of an image.
        :return: A numpy array of the image.
        """
        if isinstance(image, str):  # If image is a path to an image
            return cv.imread(image)
        if isinstance(image, np.ndarray):  # If image is already a numpy array
            return image

        raise ValueError("Input must be a path to an image or a numpy array")

    # pylint: disable=arguments-differ,arguments-renamed
    def predict_batch(
        self,
        rgb_images_and_texts_prompts: List[Tuple[Union[np.ndarray, str], List[str]]],
        box_threshold: float = 0.35,
        text_threshold: float = 0.25,
    ) -> List[pd.DataFrame]:
        """
        images: List of RGB images as NumPy arrays
        """
        # As the method is exposed to users who know nothing about the project,
        # we consider that the user may not know how to load the image, particularly
        # in RGB, and only want to provide the path of an image file
        rgb_images_and_texts_prompts = [
            (self._load_image(image), texts_prompt)
            for image, texts_prompt in rgb_images_and_texts_prompts
        ]
        if not self._are_shapes_correct(
            [image for image, texts_prompt in rgb_images_and_texts_prompts]
        ):
            raise ValueError("Incorrect received shapes")

        return super().predict_batch(
            batch=rgb_images_and_texts_prompts,
            box_threshold=box_threshold,
            text_threshold=text_threshold,
        )
