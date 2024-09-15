import uuid
from datetime import datetime
from typing import List

from core.api_exceptions import abort
from core.client.model_client.video_comparator import VideoComparatorModelClient
from core.google.cloud_run_job_manager import CloudRunJobManager
from core.google.firestore_client import FirestoreClient
from core.google.storage_client import StorageClient
from core.path import GSPath
from core.routes.video_comparator import routes
from core.schemas.asset import AssetType
from core.schemas.google.cloud_run import JobConfig
from core.schemas.video_comparator import (
    InputSampleSchema,
    OutputSampleSchema,
    VideoComparatorInput,
    VideoComparatorJobDocument,
    VideoComparatorOutput,
    VideoComparatorRealTimeInput,
    VideoComparatorRealTimeOutput,
)
from core.services.asset_reader import make_assets
from fastapi import APIRouter, Depends, Response
from starlette import status

from video_comparator.api.dependencies import (
    use_cloud_run_job_manager,
    use_config,
    use_firestore_client,
    use_firestore_jobs_collection,
    use_storage_client,
    use_video_comparator_model_client,
    use_videos_to_compare_bucket,
)
from video_comparator.config import Config
from video_comparator.environment_variables import (
    EMBEDDINGS_BUCKET,
    JOB_RESULTS_BUCKET,
    MODEL_INSTANTIATOR_HOST,
    MODEL_NAME,
    PROJECT_ID,
    REGION,
)

router = APIRouter(
    prefix=f"/{routes.VideoComparator.prefix}", tags=[routes.VideoComparator.prefix]
)


def _launched_job_response(
    response: Response,
    job_id: str,
) -> VideoComparatorOutput:
    response.status_code = status.HTTP_201_CREATED

    return VideoComparatorOutput(
        job_id=job_id,
    )


def _real_time_response(
    response: Response, output: OutputSampleSchema
) -> VideoComparatorRealTimeOutput:
    response.status_code = status.HTTP_200_OK

    return VideoComparatorRealTimeOutput(similarity_score=output.similarity_results)


def _validate_video_storage_path(video_storage_path: GSPath, expected_bucket_name: str):
    bucket_name, _ = GSPath(video_storage_path).to_bucket_and_blob_names()

    if bucket_name != expected_bucket_name:
        raise ValueError(
            f"Unexpected bucket name for storage path '{video_storage_path}', "
            f"expected {expected_bucket_name}, got {bucket_name}"
        )


def _validate_video_storage_paths(
    videos_storage_paths: List[GSPath], expected_bucket_name: str
):
    for video_storage_path in videos_storage_paths:
        _validate_video_storage_path(
            video_storage_path=video_storage_path,
            expected_bucket_name=expected_bucket_name,
        )


def _upload_job_document(
    firestore_client: FirestoreClient,
    firestore_jobs_collection: str,
    job_id: str,
    assets_ids: List[str],
):
    video_comparator_job_document = VideoComparatorJobDocument(
        job_id=job_id, job_date=datetime.utcnow(), assets_ids=assets_ids
    )
    firestore_client.upload_document(
        collection_name=firestore_jobs_collection,
        document_id=job_id,
        content=video_comparator_job_document.dict(),
    )


@router.post(
    routes.VideoComparator.compare_videos,
    status_code=status.HTTP_201_CREATED,
)
def compare_videos(
    video_comparator_input: VideoComparatorInput,
    response: Response,
    config: Config = Depends(use_config),
    cloud_run_job_manager: CloudRunJobManager = Depends(use_cloud_run_job_manager),
    storage_client: StorageClient = Depends(use_storage_client),
    firestore_client: FirestoreClient = Depends(use_firestore_client),
    firestore_jobs_collection: str = Depends(use_firestore_jobs_collection),
    videos_to_compare_bucket: str = Depends(use_videos_to_compare_bucket),
) -> VideoComparatorOutput:
    job_id = uuid.uuid4().hex

    if (
        len(video_comparator_input.videos_storage_paths)
        > config.api.maximum_videos_number
    ):
        abort(
            code=status.HTTP_400_BAD_REQUEST,
            detail=f"The number of videos exceeds the maximum currently allowed "
            f"({len(video_comparator_input.videos_storage_paths)} > "
            f"{config.api.maximum_videos_number})",
        )

    try:
        _validate_video_storage_paths(
            videos_storage_paths=video_comparator_input.videos_storage_paths,
            expected_bucket_name=videos_to_compare_bucket,
        )
    except ValueError as value_error:
        abort(code=status.HTTP_400_BAD_REQUEST, detail=str(value_error))

    video_assets = make_assets(
        assets_paths=video_comparator_input.videos_storage_paths,
        storage_client=storage_client,
        asset_type=AssetType.VIDEO,
    )
    assets_ids = [video_asset.get_hash() for video_asset in video_assets]

    _upload_job_document(
        firestore_client=firestore_client,
        firestore_jobs_collection=firestore_jobs_collection,
        job_id=job_id,
        assets_ids=assets_ids,
    )

    job_name = f"compare-videos-{job_id}"
    job_command_args = [
        "-m",
        "video_comparator.jobs.compare_videos",
    ]
    job_environment_variables = {
        "PROJECT_ID": PROJECT_ID,
        "REGION": REGION,
        "MODEL_NAME": MODEL_NAME,
        "MODEL_INSTANTIATOR_HOST": MODEL_INSTANTIATOR_HOST,
        "JOB_ID": job_id,
        "EMBEDDINGS_BUCKET": EMBEDDINGS_BUCKET,
        "JOB_RESULTS_BUCKET": JOB_RESULTS_BUCKET,
        "VIDEOS_STORAGE_PATHS": " ".join(video_comparator_input.videos_storage_paths),
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
    routes.VideoComparator.compare_videos_real_time,
    status_code=status.HTTP_200_OK,
)
def compare_videos_real_time(
    video_comparator_input: VideoComparatorRealTimeInput,
    response: Response,
    config: Config = Depends(use_config),
    video_comparator: VideoComparatorModelClient = Depends(
        use_video_comparator_model_client
    ),
    storage_client: StorageClient = Depends(use_storage_client),
    videos_to_compare_bucket: str = Depends(use_videos_to_compare_bucket),
) -> VideoComparatorRealTimeOutput:
    video_storage_path, other_video_storage_path = (
        video_comparator_input.video_storage_path,
        video_comparator_input.other_video_storage_path,
    )

    _validate_video_storage_paths(
        videos_storage_paths=[video_storage_path, other_video_storage_path],
        expected_bucket_name=videos_to_compare_bucket,
    )

    video, other_video = make_assets(
        assets_paths=[video_storage_path, other_video_storage_path],
        asset_type=AssetType.VIDEO,
        storage_client=storage_client,
        time_step=1 / config.preprocessing.fps,
        resized_shape_or_minimal_value=config.preprocessing.image_size,
    )

    output: OutputSampleSchema = video_comparator.predict_single(
        InputSampleSchema(video=video, other_video=other_video)
    )

    return _real_time_response(response=response, output=output)
