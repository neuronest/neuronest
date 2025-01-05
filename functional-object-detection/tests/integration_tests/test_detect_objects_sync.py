from core.client.object_detection import ObjectDetectionClient
from core.services.asset_reader import make_asset


# pylint: disable=unused-argument
def test_detect_objects_sync(
    object_detection_client: ObjectDetectionClient,
    sample_path: str,
    uninstantiate_teardown,
):
    batch_predictions = object_detection_client.detect_objects_sync(
        images_paths=[sample_path]
    )
    assert len(batch_predictions) == 1

    predictions = batch_predictions[0].predictions
    assert set(prediction.class_name for prediction in predictions) == {
        "dog",
        "bicycle",
        "truck",
    }

    labels_to_predict = ["dog", "bicycle"]
    batch_size = 10
    batch_predictions = object_detection_client.detect_objects_sync(
        images_paths=[sample_path] * batch_size, labels_to_predict=labels_to_predict
    )
    assert len(batch_predictions) == batch_size

    assert set(
        prediction.class_name
        for predictions in batch_predictions
        for prediction in predictions.predictions
    ) == set(labels_to_predict)

    # real time test here once the endpoint is already up

    asset = make_asset(sample_path)

    labels_to_predict = ["dog"]
    outputs = object_detection_client.detect_objects_real_time(
        image=asset.content, labels_to_predict=labels_to_predict
    )

    assert set(prediction.class_name for prediction in outputs.predictions) == set(
        labels_to_predict
    )
