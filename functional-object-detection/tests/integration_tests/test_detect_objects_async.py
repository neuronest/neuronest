from typing import List

from core.client.object_detection import ObjectDetectionClient
from core.schemas.modules.object_detection import ObjectDetectionSampleResultsDocument
from core.services.asset_reader import make_asset


# pylint: disable=unused-argument
def test_detect_objects_async(
    object_detection_client: ObjectDetectionClient,
    sample_path: str,
    uninstantiate_teardown,
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

    # real time test here once the endpoint to already up

    asset = make_asset(sample_path)

    labels_to_predict = ["dog"]
    outputs = object_detection_client.detect_objects_real_time(
        image=asset.content, labels_to_predict=labels_to_predict
    )

    assert set(prediction.class_name for prediction in outputs.predictions) == set(
        labels_to_predict
    )
