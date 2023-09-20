import os
from typing import List, Tuple

import pytest
from core.client.video_comparator import VideoComparatorClient
from core.google.storage_client import StorageClient
from core.path import GSPath


@pytest.mark.parametrize(
    "best_to_worst_matching_videos_pairs",
    [
        [
            (
                "gs://datasets-neuronest/mirror_or_not_video_archive/gimli.mp4",
                "gs://datasets-neuronest/mirror_or_not_video_archive/gimli_the_great.mp4",
            ),
            (
                "gs://datasets-neuronest/mirror_or_not_video_archive/for_frodo_alone.mp4",
                "gs://datasets-neuronest/mirror_or_not_video_archive/for_frodo.mp4",
            ),
        ],
    ],
)
def test_endpoint_inference(
    video_comparator_client: VideoComparatorClient,
    best_to_worst_matching_videos_pairs: List[Tuple[str, str]],
):
    for video_path, other_video_path in best_to_worst_matching_videos_pairs:
        video_path = GSPath(video_path)
        other_video_path = GSPath(other_video_path)

        StorageClient().download_blob_to_file(
            bucket_name=video_path.bucket,
            source_blob_name=video_path.blob_name,
            destination_file_name=video_path,
        )
        StorageClient().download_blob_to_file(
            bucket_name=other_video_path.bucket,
            source_blob_name=other_video_path.blob_name,
            destination_file_name=other_video_path,
        )

    video_comparator_best_to_worst_video_pairs = sorted(
        best_to_worst_matching_videos_pairs,
        key=lambda video_and_other_video_path: video_comparator_client.predict_batch(
            batch=[
                (
                    video_and_other_video_path[0],
                    video_and_other_video_path[1],
                )
            ],
        )[0],
        reverse=True,
    )

    assert (
        best_to_worst_matching_videos_pairs
        == video_comparator_best_to_worst_video_pairs
    )

    for video_path, other_video_path in best_to_worst_matching_videos_pairs:
        os.remove(video_path)
        os.remove(other_video_path)
