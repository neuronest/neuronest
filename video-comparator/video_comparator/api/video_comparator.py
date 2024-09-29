import uuid
from datetime import datetime
from typing import List, Tuple, cast

from core.api_exceptions import abort
from core.client.model_client.video_comparator import VideoComparatorModelClient
from core.google.cloud_run_job_manager import CloudRunJobManager
from core.google.firestore_client import FirestoreClient
from core.google.storage_client import StorageClient
from core.hashing import combine_hashes
from core.path import GSPath
from core.routes.video_comparator import routes
from core.schemas.asset import AssetType
from core.schemas.google.cloud_run import JobConfig
from core.schemas.modules.video_comparator import (
    InputSampleSchema,
    OutputSampleSchema,
    VideoComparatorInput,
    VideoComparatorJobDocument,
    VideoComparatorOutput,
    VideoComparatorRealTimeInput,
    VideoComparatorRealTimeOutput,
)
from core.services.asset_reader import make_asset, make_assets
from core.utils import contains_only_n_elements
from fastapi import APIRouter, Depends, Response
from starlette import status

from video_comparator.api.dependencies import (
    use_cloud_run_job_manager,
    use_config,
    use_firestore_client,
    use_firestore_jobs_collection,
    use_samples_bucket,
    use_storage_client,
    use_video_comparator_model_client,
)
from video_comparator.config import Config
from video_comparator.environment_variables import (
    EMBEDDINGS_BUCKET,
    MODEL_INSTANTIATOR_HOST,
    MODEL_NAME,
    PROJECT_ID,
    REGION,
    RESULTS_BUCKET,
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


def _validate_video_path_pairs(
    video_path_pairs: List[Tuple[GSPath, GSPath]], expected_bucket_name: str
):
    for video_storage_path, other_video_storage_path in video_path_pairs:
        _validate_video_storage_path(
            video_storage_path=video_storage_path,
            expected_bucket_name=expected_bucket_name,
        )
        _validate_video_storage_path(
            video_storage_path=other_video_storage_path,
            expected_bucket_name=expected_bucket_name,
        )


def _upload_job_document(
    firestore_client: FirestoreClient,
    firestore_jobs_collection: str,
    job_id: str,
    samples_ids: List[str],
):
    video_comparator_job_document = VideoComparatorJobDocument(
        job_id=job_id, job_date=datetime.utcnow(), samples_ids=samples_ids
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
    samples_bucket: str = Depends(use_samples_bucket),
) -> VideoComparatorOutput:
    job_id = uuid.uuid4().hex

    if len(video_comparator_input.samples) > config.api.maximum_elements_number:
        abort(
            code=status.HTTP_400_BAD_REQUEST,
            detail=f"The number of samples exceeds the maximum currently allowed "
            f"({len(video_comparator_input.samples)} > "
            f"{config.api.maximum_elements_number})",
        )

    if (
        all(
            contains_only_n_elements(sample.paths, n=2)
            for sample in video_comparator_input.samples
        )
        is True
    ):
        video_path_pairs = cast(
            List[Tuple[GSPath, GSPath]],
            [sample.paths for sample in video_comparator_input.samples],
        )
    else:
        return abort(
            code=status.HTTP_400_BAD_REQUEST,
            detail="At least one sample does not contains exactly two videos, "
            "which is not supported",
        )

    try:
        _validate_video_path_pairs(
            video_path_pairs=video_path_pairs,
            expected_bucket_name=samples_bucket,
        )
    except ValueError as value_error:
        abort(code=status.HTTP_400_BAD_REQUEST, detail=str(value_error))

    samples_ids = [
        combine_hashes(
            [
                make_asset(
                    asset_path=video_path,
                    storage_client=storage_client,
                    asset_type=AssetType.VIDEO,
                ).get_hash(),
                make_asset(
                    asset_path=other_video_path,
                    storage_client=storage_client,
                    asset_type=AssetType.VIDEO,
                ).get_hash(),
            ],
            reorder=False,
        )
        for video_path, other_video_path in video_path_pairs
    ]

    _upload_job_document(
        firestore_client=firestore_client,
        firestore_jobs_collection=firestore_jobs_collection,
        job_id=job_id,
        samples_ids=samples_ids,
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
        "RESULTS_BUCKET": RESULTS_BUCKET,
        "VIDEO_PATH_PAIRS": str(video_path_pairs),
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
    samples_bucket: str = Depends(use_samples_bucket),
) -> VideoComparatorRealTimeOutput:
    paths = video_comparator_input.sample.paths

    if contains_only_n_elements(paths, n=2) is True:
        video_storage_path, other_video_storage_path = paths
    else:
        return abort(
            code=status.HTTP_400_BAD_REQUEST,
            detail=f"Two and only two videos should be specified, "
            f"received {len(paths)}",
        )

    _validate_video_path_pairs(
        video_path_pairs=[(video_storage_path, other_video_storage_path)],
        expected_bucket_name=samples_bucket,
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
