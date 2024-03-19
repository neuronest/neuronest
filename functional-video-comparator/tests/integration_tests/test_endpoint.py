from typing import List, Tuple

import pytest
from core.client.video_comparator import VideoComparatorClient


# pylint: disable=unused-argument
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
    indirect=True,
)
def test_endpoint_inference(
    video_comparator_client: VideoComparatorClient,
    best_to_worst_matching_videos_pairs: List[Tuple[str, str]],
    uninstantiate_teardown,
):
    video_comparator_best_to_worst_video_pairs = sorted(
        best_to_worst_matching_videos_pairs,
        key=lambda video_and_other_video_path: video_comparator_client.predict_batch(
            batch_sample=[
                (
                    video_and_other_video_path[0],
                    video_and_other_video_path[1],
                )
            ],
        )[0].similarity,
        reverse=True,
    )

    assert (
        best_to_worst_matching_videos_pairs
        == video_comparator_best_to_worst_video_pairs
    )
