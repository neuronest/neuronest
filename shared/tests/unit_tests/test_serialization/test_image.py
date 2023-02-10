import os
from typing import List

import cv2 as cv
import numpy as np
import pytest

from core.serialization.image import (
    image_from_binary,
    image_from_string,
    image_to_binary,
    image_to_string,
)


@pytest.fixture(name="images_directory")
def fixture_images_directory() -> str:
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "data",
    )


@pytest.fixture(name="images")
def fixture_images(images_directory: str) -> List[np.ndarray]:
    return [
        cv.imread(os.path.join(images_directory, image_path))
        for image_path in os.listdir(images_directory)
    ]


def test_image_binary(images: List[np.ndarray]):
    for image in images:
        assert np.array_equal(image_from_binary(image_to_binary(image)), image)


def test_image_string(images: List[np.ndarray]):
    for image in images:
        assert np.array_equal(image_from_string(image_to_string(image)), image)
