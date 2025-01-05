from typing import List, Tuple

import pytest
from core.client.video_comparator import VideoComparatorClient
from core.google.storage_client import StorageClient
from core.schemas.asset import AssetType
from core.schemas.modules.video_comparator import (
    VideoComparatorRealTimeOutput,
    VideoComparatorSampleResultsDocument,
)
from core.services.asset_reader import make_asset


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
)
def test_compare_videos_sync(
    video_comparator_client: VideoComparatorClient,
    storage_client: StorageClient,
    best_to_worst_matching_videos_pairs: List[Tuple[str, str]],
    uninstantiate_teardown,
):
    assets_pairs = [
        (
            make_asset(
                asset_path=first_video_path,
                asset_type=AssetType.VIDEO,
                storage_client=storage_client,
            ),
            make_asset(
                asset_path=second_video_path,
                asset_type=AssetType.VIDEO,
                storage_client=storage_client,
            ),
        )
        for (first_video_path, second_video_path) in best_to_worst_matching_videos_pairs
    ]

    all_samples_results: List[VideoComparatorSampleResultsDocument] = (
        video_comparator_client.compare_videos_sync(
            video_path_pairs=[
                (assets_pair[0].asset_path, assets_pair[1].asset_path)
                for assets_pair in assets_pairs
            ]
        )
    )

    similarities = [
        sample_result.similarity_score for sample_result in all_samples_results
    ]

    assert len(similarities) == 2
    assert 0.0 not in similarities and 1.0 not in similarities
    assert similarities[0] < similarities[1]

    # real time test here once the endpoint is already up

    outputs: List[VideoComparatorRealTimeOutput] = [
        video_comparator_client.compare_videos_real_time(
            video_path=first_video.asset_path, other_video_path=second_video.asset_path
        )
        for (first_video, second_video) in assets_pairs
    ]

    similarities = [sample_result.similarity_score for sample_result in outputs]

    assert len(similarities) == 2
    assert 0.0 not in similarities and 1.0 not in similarities
    assert similarities[0] < similarities[1]
