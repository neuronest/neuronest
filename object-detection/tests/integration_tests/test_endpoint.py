import os

import cv2 as cv
import numpy as np
import pytest
from core.client.object_detection import ObjectDetectionClient
from core.google.vertex_ai_manager import VertexAIManager
from omegaconf import DictConfig

from object_detection.config import cfg
from object_detection.environment_variables import (
    GOOGLE_APPLICATION_CREDENTIALS,
    PROJECT_ID,
)
from tests.injection.fake_model_instantiator_client import FakeModelInstantiatorClient


@pytest.fixture(name="config")
def fixture_config() -> DictConfig:
    return cfg


@pytest.fixture(name="image_directory")
def fixture_image_directory() -> str:
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"
    )


@pytest.fixture(name="image")
def fixture_sample(image_directory: str) -> np.ndarray:
    return cv.imread(os.path.join(image_directory, "sample.png"))


@pytest.fixture(name="vertex_ai_manager")
def fixture_vertex_ai_manager(config: DictConfig) -> VertexAIManager:
    return VertexAIManager(
        location=config.region,
        key_path=GOOGLE_APPLICATION_CREDENTIALS,
        project_id=PROJECT_ID,
    )


def test_endpoint_inference(
    config: DictConfig, vertex_ai_manager: VertexAIManager, image: np.ndarray
):
    model_name = config.model.name

    fake_model_instantiator_client = FakeModelInstantiatorClient(
        key_path=GOOGLE_APPLICATION_CREDENTIALS, host="fake_model_instantiator_host"
    )
    vertex_ai_manager = VertexAIManager(
        key_path=GOOGLE_APPLICATION_CREDENTIALS, location=cfg.region
    )
    object_detection_client = ObjectDetectionClient(
        vertex_ai_manager=vertex_ai_manager,
        model_instantiator_client=fake_model_instantiator_client,
        model_name=model_name,
    )

    single_prediction_df = object_detection_client.predict_single(image)
    assert set(single_prediction_df.class_name) == {"dog", "bicycle", "truck"}

    batch_predictions_df = object_detection_client.predict_batch([image, image])
    assert set(
        batch_prediction_df.class_name for batch_prediction_df in batch_predictions_df
    ) == {"dog", "bicycle", "truck"}
