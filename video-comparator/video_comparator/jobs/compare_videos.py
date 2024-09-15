import itertools
from typing import List

import numpy as np
from core.client.model_client.video_comparator import VideoComparatorModelClient
from core.google.storage_client import StorageClient
from core.schemas.asset import AssetType, VideoAsset
from core.schemas.video_comparator import InputSampleSchema, OutputSampleSchema
from core.services.asset_reader import make_assets
from core.tools import unflatten_iterable

from video_comparator.jobs.environment_variables import (
    EMBEDDINGS_BUCKET,
    JOB_ID,
    JOB_RESULTS_BUCKET,
    MODEL_INSTANTIATOR_HOST,
    MODEL_NAME,
    PROJECT_ID,
    REGION,
    VIDEOS_STORAGE_PATHS,
)
from video_comparator.jobs.services import (
    create_embedding_manager,
    create_job_results_manager,
    create_storage_client,
    create_video_comparator_model_client,
)
from video_comparator.services.embedding_manager import EmbeddingManager


def compare_first_video_to_others(
    video_assets: List[VideoAsset],
    existing_embeddings: List[np.ndarray],
    video_comparator_model_client: VideoComparatorModelClient,
) -> List[OutputSampleSchema]:
    first_video_asset, first_existing_embedding = (
        video_assets[0],
        existing_embeddings[0],
    )
    first_batch = [
        InputSampleSchema(
            video=first_video_asset if first_existing_embedding is None else None,
            other_video=video_asset if existing_embedding is None else None,
            video_embedding=first_existing_embedding,
            other_video_embedding=existing_embedding,
        )
        for video_asset, existing_embedding in zip(
            video_assets[1:], existing_embeddings[1:]
        )
    ]

    return video_comparator_model_client.predict_batch(samples=first_batch)


def compare_remaining_videos_to_others(
    first_video_to_others_outputs: List[OutputSampleSchema],
    video_comparator_model_client: VideoComparatorModelClient,
) -> List[OutputSampleSchema]:
    remaining_batch = [
        InputSampleSchema(
            video_embedding=left_video.other_video_embedding,
            other_video_embedding=right_video.other_video_embedding,
        )
        for left_video, right_video in itertools.combinations(
            first_video_to_others_outputs, 2
        )
    ]

    return video_comparator_model_client.predict_batch(samples=remaining_batch)


def create_similarities_matrix(
    first_video_to_others_outputs: List[OutputSampleSchema],
    remaining_videos_to_others_outputs: List[OutputSampleSchema],
) -> np.ndarray:
    unflattened_remaining_videos_to_others_outputs = list(
        unflatten_iterable(
            remaining_videos_to_others_outputs,
            sizes=list(range(len(first_video_to_others_outputs) - 1, 0, -1)),
        )
    )
    unflattened_outputs = [
        first_video_to_others_outputs
    ] + unflattened_remaining_videos_to_others_outputs

    videos_number = len(first_video_to_others_outputs) + 1

    scores_matrix = np.full((videos_number, videos_number), 1)
    for i, batch_outputs in enumerate(unflattened_outputs):
        for j, batch_output in enumerate(batch_outputs):
            scores_matrix[i, j + i + 1] = batch_output.similarity_results
            scores_matrix[j + i + 1, i] = batch_output.similarity_results

    return scores_matrix


def run_videos_comparisons(
    storage_client: StorageClient,
    embedding_manager: EmbeddingManager,
    video_comparator_model_client: VideoComparatorModelClient,
    videos_storage_paths: List[str],
) -> np.ndarray:
    if len(videos_storage_paths) == 0:
        return np.array([], dtype=np.float32)

    video_assets = make_assets(
        assets_paths=videos_storage_paths,
        storage_client=storage_client,
        asset_type=AssetType.VIDEO,
    )
    assets_ids = [video_asset.get_hash() for video_asset in video_assets]

    existing_embeddings = [
        embedding_manager.retrieve_embedding(asset_id=asset_id, is_missing_ok=True)
        for asset_id in assets_ids
    ]

    # we compare the first video with all the others in a first batch in order to
    # compute the embeddings once for all
    first_video_to_others_outputs = compare_first_video_to_others(
        video_assets=video_assets,
        existing_embeddings=existing_embeddings,
        video_comparator_model_client=video_comparator_model_client,
    )

    embedding_manager.store_embedding(
        asset_id=assets_ids[0],
        embedding=first_video_to_others_outputs[0].video_embedding,
    )
    embedding_manager.store_multiple_embeddings(
        asset_ids=assets_ids[1:],
        embeddings=[
            first_batch_output.other_video_embedding
            for first_batch_output in first_video_to_others_outputs
        ],
    )

    remaining_videos_to_others_outputs = compare_remaining_videos_to_others(
        first_video_to_others_outputs=first_video_to_others_outputs,
        video_comparator_model_client=video_comparator_model_client,
    )

    return create_similarities_matrix(
        first_video_to_others_outputs=first_video_to_others_outputs,
        remaining_videos_to_others_outputs=remaining_videos_to_others_outputs,
    )


def main(
    project_id: str,
    region: str,
    model_name: str,
    model_instantiator_host: str,
    job_id: str,
    embeddings_bucket: str,
    job_results_bucket: str,
    videos_storage_paths: List[str],
):
    storage_client = create_storage_client(project_id=project_id)
    embedding_manager = create_embedding_manager(
        storage_client=storage_client, bucket_name=embeddings_bucket
    )
    job_results_manager = create_job_results_manager(
        storage_client=storage_client, bucket_name=job_results_bucket
    )
    video_comparator_model_client = create_video_comparator_model_client(
        project_id=project_id,
        region=region,
        model_instantiator_host=model_instantiator_host,
        model_name=model_name,
    )

    similarities = run_videos_comparisons(
        storage_client=storage_client,
        embedding_manager=embedding_manager,
        video_comparator_model_client=video_comparator_model_client,
        videos_storage_paths=videos_storage_paths,
    )

    job_results_manager.store_results(job_id=job_id, results=similarities)


if __name__ == "__main__":
    main(
        project_id=PROJECT_ID,
        region=REGION,
        model_name=MODEL_NAME,
        model_instantiator_host=MODEL_INSTANTIATOR_HOST,
        job_id=JOB_ID,
        embeddings_bucket=EMBEDDINGS_BUCKET,
        job_results_bucket=JOB_RESULTS_BUCKET,
        videos_storage_paths=VIDEOS_STORAGE_PATHS,
    )
