import os

import numpy as np
import pandas as pd
import pytest
from core.google.vertex_ai_manager import VertexAIManager
from core.serialization.array import array_from_string
from core.serialization.image import image_to_string
from cv2 import cv2 as cv
from omegaconf import DictConfig

from object_detection.config import cfg
from object_detection.environment_variables import GOOGLE_APPLICATION_CREDENTIALS
from object_detection.modules.schemas import PREDICTION_COLUMNS, OutputSchema


@pytest.fixture(name="config")
def fixture_config() -> DictConfig:
    return cfg


@pytest.fixture(name="image_directory")
def fixture_image_directory() -> str:
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


@pytest.fixture(name="image")
def fixture_sample(image_directory: str) -> np.ndarray:
    return cv.imread(os.path.join(image_directory, "sample.png"))


@pytest.fixture(name="vertex_ai_manager")
def fixture_vertex_ai_manager(config: DictConfig) -> VertexAIManager:
    return VertexAIManager(
        key_path=GOOGLE_APPLICATION_CREDENTIALS, location=config.region
    )


def test_endpoint_inference(
    config: DictConfig, vertex_ai_manager: VertexAIManager, image: np.ndarray
):
    model_name = config.model.name

    endpoint = vertex_ai_manager.get_last_endpoint_by_name(model_name)
    raw_predictions = endpoint.predict([{"data": image_to_string(image)}])
    predictions = array_from_string(
        OutputSchema.parse_obj(raw_predictions.predictions[0]).results
    )

    assert isinstance(predictions, np.ndarray)

    predictions_df = pd.DataFrame(predictions, columns=PREDICTION_COLUMNS)

    assert set(predictions_df.class_name) == {"dog", "bicycle", "truck"}
