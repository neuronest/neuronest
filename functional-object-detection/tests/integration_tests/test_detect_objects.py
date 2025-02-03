from typing import List

from core.client.object_detection import ObjectDetectionClient
from core.schemas.modules.object_detection import ObjectDetectionSampleResultsDocument
from core.services.asset_reader import make_asset
from joblib import Parallel, delayed


def _test_detect_objects_sync(
    object_detection_client: ObjectDetectionClient,
    sample_path: str,
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


def _test_detect_objects_async(
    object_detection_client: ObjectDetectionClient,
    sample_path: str,
):
    labels_to_predict = ["truck", "bicycle"]
    batch_size = 10
    outputs = object_detection_client.detect_objects_async(
        images_paths=[sample_path] * batch_size, labels_to_predict=labels_to_predict
    )

    job_results_documents = [
        object_detection_client.get_predictions_from_job_id(
            job_id=output.job_id, wait_if_not_existing=True
        )
        for output in outputs
    ]
    all_samples_results: List[ObjectDetectionSampleResultsDocument] = [
        sample_results
        for job_results_document in job_results_documents
        for sample_results in job_results_document.results
    ]

    assert set(
        prediction.class_name
        for predictions in all_samples_results
        for prediction in predictions.predictions
    ) == set(labels_to_predict)


def _test_detect_objects_real_time(
    object_detection_client: ObjectDetectionClient,
    sample_path: str,
):
    asset = make_asset(sample_path)

    labels_to_predict = ["dog"]
    outputs = object_detection_client.detect_objects_real_time(
        image=asset.content, labels_to_predict=labels_to_predict
    )

    assert set(prediction.class_name for prediction in outputs.predictions) == set(
        labels_to_predict
    )


# pylint: disable=unused-argument
def test_detect_objects_sync_async_real_time(
    object_detection_client: ObjectDetectionClient,
    sample_path: str,
    uninstantiate_teardown,
):
    test_functions = (
        _test_detect_objects_sync,
        _test_detect_objects_async,
    )

    Parallel(n_jobs=-1, prefer="threads")(
        delayed(test_function)(
            object_detection_client=object_detection_client, sample_path=sample_path
        )
        for test_function in test_functions
    )

    # executed once the endpoint is ready for the real-time part, thus avoiding a
    # timeout
    _test_detect_objects_real_time(
        object_detection_client=object_detection_client, sample_path=sample_path
    )
