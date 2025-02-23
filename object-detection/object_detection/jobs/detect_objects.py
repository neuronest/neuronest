import ast
import logging
import os
from typing import List, Tuple

from core.client.abstract.prediction_api_client import make_results_blob_name
from core.path import GSPath
from core.schemas.asset import AssetType
from core.schemas.modules.object_detection import (
    InputSampleSchema,
    ObjectDetectionSampleResultsDocument,
    OutputPrediction,
    OutputSampleSchema,
    SampleMetadata,
)
from core.services.asset_reader import make_asset
from joblib import Parallel, delayed

from object_detection.jobs.environment_variables import (
    IMAGES_STORAGE_PATHS,
    JOB_ID,
    MODEL_INSTANTIATOR_HOST,
    MODEL_NAME,
    PROJECT_ID,
    RESULTS_BUCKET,
    SAMPLE_METADATA,
    VERTEX_LOCATION,
)
from object_detection.jobs.services import (
    create_object_detection_model_client,
    create_storage_client,
)

logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)


def run_objects_detection(
    project_id: str,
    vertex_location: str,
    results_bucket: str,
    model_instantiator_host: str,
    job_id: str,
    model_name: str,
    image_storage_path: GSPath,
    sample_metadata: SampleMetadata,
):
    storage_client = create_storage_client(project_id=project_id)
    object_detection_model_client = create_object_detection_model_client(
        project_id=project_id,
        vertex_location=vertex_location,
        model_instantiator_host=model_instantiator_host,
        model_name=model_name,
    )

    image_asset = make_asset(
        asset_path=image_storage_path,
        storage_client=storage_client,
        asset_type=AssetType.IMAGE,
    )
    sample_id = image_asset.get_hash()

    output: OutputSampleSchema = object_detection_model_client.predict_single(
        sample=InputSampleSchema(
            image=image_asset.content, sample_metadata=sample_metadata
        )
    )

    logger.info(
        f"Image with hash='{sample_id}', sample_metadata='{sample_metadata}' "
        f"-> output='{output.results.to_dict()}'"
    )

    predictions = [
        OutputPrediction.model_validate(output_prediction)
        for output_prediction in output.results.to_dict(orient="records")
    ]
    objects_detection_document = ObjectDetectionSampleResultsDocument(
        sample_id=sample_id, job_id=job_id, predictions=predictions
    )

    storage_client.upload_blob_from_dict(
        bucket_name=results_bucket,
        blob_name=make_results_blob_name(job_id=job_id, sample_id=sample_id),
        content=objects_detection_document.model_dump(),
    )


def main(
    project_id: str,
    vertex_location: str,
    model_name: str,
    model_instantiator_host: str,
    job_id: str,
    results_bucket: str,
    images_storage_paths: List[Tuple[str, str]],
    sample_metadata: SampleMetadata,
):
    if len(images_storage_paths) == 0:
        raise ValueError("The received list of images paths is empty")

    return Parallel(n_jobs=os.cpu_count())(
        delayed(run_objects_detection)(
            project_id=project_id,
            vertex_location=vertex_location,
            results_bucket=results_bucket,
            model_instantiator_host=model_instantiator_host,
            job_id=job_id,
            model_name=model_name,
            image_storage_path=GSPath(image_storage_path),
            sample_metadata=sample_metadata,
        )
        for image_storage_path in images_storage_paths
    )


if __name__ == "__main__":
    main(
        project_id=PROJECT_ID,
        vertex_location=VERTEX_LOCATION,
        model_name=MODEL_NAME,
        model_instantiator_host=MODEL_INSTANTIATOR_HOST,
        job_id=JOB_ID,
        results_bucket=RESULTS_BUCKET,
        images_storage_paths=ast.literal_eval(IMAGES_STORAGE_PATHS),
        sample_metadata=SampleMetadata.model_validate_json(SAMPLE_METADATA),
    )
