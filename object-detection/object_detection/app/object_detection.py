import uuid
from datetime import datetime
from typing import List

from core.api_exceptions import abort
from core.client.model_client.object_detection import ObjectDetectionModelClient
from core.google.cloud_run_job_manager import CloudRunJobManager
from core.google.firestore_client import FirestoreClient
from core.google.storage_client import StorageClient
from core.path import GSPath
from core.routes.object_detection import routes
from core.schemas.asset import AssetType
from core.schemas.google.cloud_run import JobConfig
from core.schemas.modules.object_detection import (
    InputSampleSchema,
    ObjectDetectionInput,
    ObjectDetectionJobDocument,
    ObjectDetectionOutput,
    ObjectDetectionRealTimeInlineInput,
    ObjectDetectionRealTimeOutput,
    OutputPrediction,
    OutputSampleSchema,
)
from core.serialization.image import image_from_string
from core.services.asset_reader import make_assets
from core.utils import contains_only_one_element
from fastapi import APIRouter, Depends, Response
from starlette import status

from object_detection.app.dependencies import (
    use_cloud_run_job_manager,
    use_config,
    use_firestore_client,
    use_firestore_jobs_collection,
    use_object_detection_model_client,
    use_samples_bucket,
    use_storage_client,
)
from object_detection.config import Config
from object_detection.environment_variables import (
    MODEL_INSTANTIATOR_HOST,
    MODEL_NAME,
    PROJECT_ID,
    REGION,
    RESULTS_BUCKET,
    VPC_NETWORK,
)

router = APIRouter(
    prefix=f"/{routes.ObjectDetection.prefix}", tags=[routes.ObjectDetection.prefix]
)


def _launched_job_response(
    response: Response,
    job_id: str,
) -> ObjectDetectionOutput:
    response.status_code = status.HTTP_201_CREATED

    return ObjectDetectionOutput(
        job_id=job_id,
    )


def _real_time_response(
    response: Response, output: OutputSampleSchema
) -> ObjectDetectionRealTimeOutput:
    response.status_code = status.HTTP_200_OK

    return ObjectDetectionRealTimeOutput(
        predictions=[
            OutputPrediction.model_validate(output_prediction)
            for output_prediction in output.results.to_dict(orient="records")
        ]
    )


def _validate_image_storage_path(image_storage_path: GSPath, expected_bucket_name: str):
    bucket_name, _ = GSPath(image_storage_path).to_bucket_and_blob_names()

    if bucket_name != expected_bucket_name:
        raise ValueError(
            f"Unexpected bucket name for storage path '{image_storage_path}', "
            f"expected {expected_bucket_name}, got {bucket_name}"
        )


def _validate_images_storage_paths(
    images_storage_paths: List[GSPath], expected_bucket_name: str
):
    for image_storage_path in images_storage_paths:
        _validate_image_storage_path(
            image_storage_path=image_storage_path,
            expected_bucket_name=expected_bucket_name,
        )


def _upload_job_document(
    firestore_client: FirestoreClient,
    firestore_jobs_collection: str,
    job_id: str,
    samples_ids: List[str],
):
    object_detection_job_document = ObjectDetectionJobDocument(
        job_id=job_id, job_date=datetime.utcnow(), samples_ids=samples_ids
    )
    firestore_client.upload_document(
        collection_name=firestore_jobs_collection,
        document_id=job_id,
        content=object_detection_job_document.model_dump(),
    )


@router.post(
    routes.ObjectDetection.detect_objects,
    status_code=status.HTTP_201_CREATED,
)
def detect_objects(
    object_detection_input: ObjectDetectionInput,
    response: Response,
    config: Config = Depends(use_config),
    cloud_run_job_manager: CloudRunJobManager = Depends(use_cloud_run_job_manager),
    storage_client: StorageClient = Depends(use_storage_client),
    firestore_client: FirestoreClient = Depends(use_firestore_client),
    firestore_jobs_collection: str = Depends(use_firestore_jobs_collection),
    samples_bucket: str = Depends(use_samples_bucket),
) -> ObjectDetectionOutput:
    job_id = uuid.uuid4().hex

    if len(object_detection_input.samples) > config.app.maximum_elements_number:
        abort(
            code=status.HTTP_400_BAD_REQUEST,
            detail=f"The number of samples exceeds the maximum currently allowed "
            f"({len(object_detection_input.samples)} > "
            f"{config.app.maximum_elements_number})",
        )

    if (
        all(
            contains_only_one_element(sample.paths)
            for sample in object_detection_input.samples
        )
        is True
    ):
        images_storage_paths = [
            sample.paths[0] for sample in object_detection_input.samples
        ]
    else:
        return abort(
            code=status.HTTP_400_BAD_REQUEST,
            detail="At least one sample contains multiple images, "
            "which is not supported",
        )

    try:
        _validate_images_storage_paths(
            images_storage_paths=images_storage_paths,
            expected_bucket_name=samples_bucket,
        )
    except ValueError as value_error:
        abort(code=status.HTTP_400_BAD_REQUEST, detail=str(value_error))

    images_assets = make_assets(
        assets_paths=images_storage_paths,
        storage_client=storage_client,
        asset_type=AssetType.IMAGE,
    )
    assets_ids = [image_asset.get_hash() for image_asset in images_assets]

    _upload_job_document(
        firestore_client=firestore_client,
        firestore_jobs_collection=firestore_jobs_collection,
        job_id=job_id,
        samples_ids=assets_ids,
    )

    job_name = f"detect-objects-{job_id}"
    job_command_args = [
        "-m",
        "object_detection.jobs.detect_objects",
    ]
    job_environment_variables = {
        "PROJECT_ID": PROJECT_ID,
        "REGION": REGION,
        "VPC_NETWORK": VPC_NETWORK,
        "MODEL_NAME": MODEL_NAME,
        "MODEL_INSTANTIATOR_HOST": MODEL_INSTANTIATOR_HOST,
        "JOB_ID": job_id,
        "RESULTS_BUCKET": RESULTS_BUCKET,
        "IMAGES_STORAGE_PATHS": str(images_storage_paths),
        "SAMPLE_METADATA": object_detection_input.sample_metadata.model_dump_json(),
    }

    cloud_run_job_manager.create_job(
        job_name=job_name,
        job_config=JobConfig(
            container_uri=config.job.container_uri,
            cpu=config.job.cpu,
            memory=config.job.memory,
            command=["python"],
            command_args=job_command_args,
            environment_variables=job_environment_variables,
        ),
        override_if_existing=True,
    )
    cloud_run_job_manager.run_job(job_name=job_name)

    return _launched_job_response(
        response=response,
        job_id=job_id,
    )


@router.post(
    routes.ObjectDetection.detect_objects_real_time,
    status_code=status.HTTP_200_OK,
)
def detect_objects_real_time(
    object_detection_input: ObjectDetectionRealTimeInlineInput,
    response: Response,
    object_detection: ObjectDetectionModelClient = Depends(
        use_object_detection_model_client
    ),
) -> ObjectDetectionRealTimeOutput:
    serialized_image = object_detection_input.inline_sample.element
    metadata = object_detection_input.sample_metadata

    image = image_from_string(serialized_image)

    output: OutputSampleSchema = object_detection.predict_single(
        InputSampleSchema(image=image, sample_metadata=metadata)
    )

    return _real_time_response(response=response, output=output)
