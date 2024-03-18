import numpy as np
from core.client.object_detection import ObjectDetectionClient


# pylint: disable=unused-argument
def test_endpoint_inference(
    object_detection_client: ObjectDetectionClient,
    image: np.ndarray,
    uninstantiate_teardown,
):
    single_prediction_df = object_detection_client.predict_single(image)
    assert set(single_prediction_df.class_name) == {"dog", "bicycle", "truck"}

    batch_predictions_df = [
        batch_prediction.results
        for batch_prediction in object_detection_client.predict_batch([image] * 10)
    ]
    assert set(
        class_name
        for batch_prediction_df in batch_predictions_df
        for class_name in batch_prediction_df.class_name
    ) == {"dog", "bicycle", "truck"}
