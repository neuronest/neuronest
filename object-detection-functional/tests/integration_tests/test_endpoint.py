import os

import cv2 as cv
import numpy as np
import pytest
from core.client.object_detection import ObjectDetectionClient
from core.google.vertex_ai_manager import VertexAIManager
from tests.environment_variables import (
    GOOGLE_APPLICATION_CREDENTIALS,
    MODEL_NAME,
    PROJECT_ID,
    REGION,
)
from tests.injection.fake_model_instantiator_client import FakeModelInstantiatorClient


@pytest.fixture(name="image_directory")
def fixture_image_directory() -> str:
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"
    )


@pytest.fixture(name="image")
def fixture_sample(image_directory: str) -> np.ndarray:
    return cv.imread(os.path.join(image_directory, "sample.png"))


@pytest.fixture(name="vertex_ai_manager")
def fixture_vertex_ai_manager() -> VertexAIManager:
    return VertexAIManager(
        location=REGION,
        key_path=GOOGLE_APPLICATION_CREDENTIALS,
        project_id=PROJECT_ID,
    )


def test_endpoint_inference(vertex_ai_manager: VertexAIManager, image: np.ndarray):

    fake_model_instantiator_client = FakeModelInstantiatorClient(
        key_path=GOOGLE_APPLICATION_CREDENTIALS, host="fake_model_instantiator_host"
    )
    vertex_ai_manager = VertexAIManager(
        key_path=GOOGLE_APPLICATION_CREDENTIALS, location=REGION, project_id=PROJECT_ID
    )
    object_detection_client = ObjectDetectionClient(
        vertex_ai_manager=vertex_ai_manager,
        model_instantiator_client=fake_model_instantiator_client,
        model_name=MODEL_NAME,
    )

    single_prediction_df = object_detection_client.predict_single(image)
    assert set(single_prediction_df.class_name) == {"dog", "bicycle", "truck"}

    batch_predictions_df = object_detection_client.predict_batch([image] * 10)
    assert set(
        class_name
        for batch_prediction_df in batch_predictions_df
        for class_name in batch_prediction_df.class_name
    ) == {"dog", "bicycle", "truck"}