import ast
import os
from typing import List, Tuple

from core.client.abstract.prediction_api_client import make_results_blob_name
from core.hashing import combine_hashes
from core.path import GSPath
from core.schemas.asset import AssetType
from core.schemas.modules.video_comparator import (
    InputSampleSchema,
    OutputSampleSchema,
    VideoComparatorSampleResultsDocument,
)
from core.services.asset_reader import make_assets
from joblib import Parallel, delayed

from video_comparator.config import cfg
from video_comparator.jobs.environment_variables import (
    EMBEDDINGS_BUCKET,
    JOB_ID,
    MODEL_INSTANTIATOR_HOST,
    MODEL_NAME,
    PROJECT_ID,
    RESULTS_BUCKET,
    VERTEX_LOCATION,
    VIDEO_PATH_PAIRS,
)
from video_comparator.jobs.services import (
    create_embedding_manager,
    create_storage_client,
    create_video_comparator_model_client,
)


def run_videos_comparison(
    video_storage_path: GSPath,
    other_video_storage_path: GSPath,
    project_id: str,
    vertex_location: str,
    embeddings_bucket: str,
    results_bucket: str,
    model_instantiator_host: str,
    job_id: str,
    model_name: str,
):
    storage_client = create_storage_client(project_id=project_id)
    embedding_manager = create_embedding_manager(
        storage_client=storage_client, bucket_name=embeddings_bucket
    )
    video_comparator_model_client = create_video_comparator_model_client(
        project_id=project_id,
        vertex_location=vertex_location,
        model_instantiator_host=model_instantiator_host,
        model_name=model_name,
    )

    video_asset, other_video_asset = make_assets(
        assets_paths=[video_storage_path, other_video_storage_path],
        asset_type=AssetType.VIDEO,
        storage_client=storage_client,
        time_step=1 / cfg.preprocessing.fps,
        resized_shape_or_minimal_value=cfg.preprocessing.image_size,
    )
    video_asset_id, other_video_asset_id = (
        video_asset.get_hash(),
        other_video_asset.get_hash(),
    )

    sample_id = combine_hashes(
        hashes=[video_asset_id, other_video_asset_id], reorder=False
    )

    (
        video_asset_existing_embedding,
        other_video_asset_existing_embedding,
    ) = embedding_manager.retrieve_multiple_embeddings(
        asset_ids=[video_asset_id, other_video_asset_id], is_missing_ok=True
    )

    prediction: OutputSampleSchema = video_comparator_model_client.predict_single(
        sample=InputSampleSchema(
            video_path=(
                video_storage_path if video_asset_existing_embedding is None else None
            ),
            other_video_path=(
                other_video_storage_path
                if other_video_asset_existing_embedding is None
                else None
            ),
            video_embedding=video_asset_existing_embedding,
            other_video_embedding=other_video_asset_existing_embedding,
        )
    )

    embedding_manager.store_multiple_embeddings(
        asset_ids=[video_asset_id, other_video_asset_id],
        embeddings=[prediction.video_embedding, prediction.other_video_embedding],
    )

    video_comparator_document = VideoComparatorSampleResultsDocument(
        sample_id=sample_id,
        job_id=job_id,
        similarity_score=prediction.similarity_score,
    )
    storage_client.upload_blob_from_dict(
        bucket_name=results_bucket,
        blob_name=make_results_blob_name(job_id=job_id, sample_id=sample_id),
        content=video_comparator_document.dict(),
    )


def main(
    project_id: str,
    vertex_location: str,
    model_name: str,
    model_instantiator_host: str,
    job_id: str,
    embeddings_bucket: str,
    results_bucket: str,
    video_path_pairs: List[Tuple[str, str]],
):
    if len(video_path_pairs) == 0:
        raise ValueError("The received list of video paths pairs has a length of 0")

    return Parallel(n_jobs=os.cpu_count())(
        delayed(run_videos_comparison)(
            video_storage_path=GSPath(video_storage_path),
            other_video_storage_path=GSPath(other_video_storage_path),
            project_id=project_id,
            vertex_location=vertex_location,
            embeddings_bucket=embeddings_bucket,
            results_bucket=results_bucket,
            model_instantiator_host=model_instantiator_host,
            job_id=job_id,
            model_name=model_name,
        )
        for video_storage_path, other_video_storage_path in video_path_pairs
    )


if __name__ == "__main__":
    main(
        project_id=PROJECT_ID,
        vertex_location=VERTEX_LOCATION,
        model_name=MODEL_NAME,
        model_instantiator_host=MODEL_INSTANTIATOR_HOST,
        job_id=JOB_ID,
        embeddings_bucket=EMBEDDINGS_BUCKET,
        results_bucket=RESULTS_BUCKET,
        video_path_pairs=ast.literal_eval(VIDEO_PATH_PAIRS),
    )
