from core.client.model_instantiator import ModelInstantiatorClient
from core.client.object_detection import ObjectDetectionClient
from core.google.vertex_ai_manager import VertexAIManager

from people_counting.config import config
from people_counting.environment_variables import (
    GOOGLE_APPLICATION_CREDENTIALS,
    MODEL_INSTANTIATOR_HOST,
    OBJECT_DETECTION_MODEL_NAME,
    REGION,
)
from people_counting.people_counter import PeopleCounter


def get_object_detection_client() -> ObjectDetectionClient:
    return ObjectDetectionClient(
        vertex_ai_manager=VertexAIManager(
            key_path=GOOGLE_APPLICATION_CREDENTIALS,
            location=REGION,
        ),
        model_instantiator_client=ModelInstantiatorClient(
            key_path=GOOGLE_APPLICATION_CREDENTIALS,
            host=MODEL_INSTANTIATOR_HOST,
        ),
        model_name=OBJECT_DETECTION_MODEL_NAME,
    )


def get_people_counter_with_package_config() -> PeopleCounter:
    return PeopleCounter(
        object_detection_client=get_object_detection_client(),
        confidence_threshold=config.postprocessing.confidence_threshold,
        algorithm_config=config.algorithm,
        image_width=config.preprocessing.image_width,
        video_outputs_directory=config.paths.outputs_directory,
    )
