from core.client.object_detection import ObjectDetectionClient
from core.services.asset_reader import make_asset


# pylint: disable=unused-argument
def test_detect_objects_real_time(
    object_detection_client: ObjectDetectionClient,
    sample_path: str,
    uninstantiate_teardown,
):
    asset = make_asset(sample_path)

    labels_to_predict = ["dog"]
    outputs = object_detection_client.detect_objects_real_time(
        image=asset.content, labels_to_predict=labels_to_predict
    )

    assert set(prediction.class_name for prediction in outputs.predictions) == set(
        labels_to_predict
    )
