import math
from typing import Tuple, Union

import cv2 as cv
import numpy as np


def get_targeted_shape(
    image_shape: Tuple[int, ...],
    resized_shape_or_minimal_value: Union[int, Tuple[int, int]],
) -> Tuple[int, int]:
    if isinstance(resized_shape_or_minimal_value, int):
        min_size = np.min(image_shape[:2])
        ratio = resized_shape_or_minimal_value / min_size

        return math.ceil(image_shape[0] * ratio), math.ceil(image_shape[1] * ratio)

    return resized_shape_or_minimal_value


def resize_image(
    image: np.ndarray, resized_shape_or_minimal_value: Union[int, Tuple[int, int]]
) -> np.ndarray:
    """targeted_dim: (height, width)"""
    targeted_shape = get_targeted_shape(
        image_shape=image.shape,
        resized_shape_or_minimal_value=resized_shape_or_minimal_value,
    )

    if targeted_shape == image.shape:
        return image

    return cv.resize(
        image, tuple(np.maximum(targeted_shape[::-1], 1)), interpolation=cv.INTER_AREA
    )
