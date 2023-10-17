from typing import List

import pytest
from core.client.people_counting import PeopleCountingClient
from core.google.storage_client import StorageClient
from core.path import GSPath
from core.schemas.asset import AssetType
from core.services.asset_reader import make_assets

from tests.integration_tests.common import are_detections_correct


@pytest.mark.parametrize(
    "videos_storage_paths, up_amounts, down_amounts",
    [
        (
            [
                GSPath("gs://datasets-neuronest/on_off_bus_videos/example_up.mp4"),
                GSPath("gs://datasets-neuronest/on_off_bus_videos/example_down.avi"),
            ],
            [4, 0],
            [0, 4],
        )
    ],
)
# pylint: disable=unused-argument
def test_count_people_sync(
    people_counting_client: PeopleCountingClient,
    storage_client: StorageClient,
    videos_storage_paths: List[GSPath],
    up_amounts: List[int],
    down_amounts: List[int],
    uninstantiate_teardown,
):
    assets = make_assets(
        assets_paths=videos_storage_paths,
        asset_type=AssetType.VIDEO,
        storage_client=storage_client,
    )

    multiple_real_time_predictions = people_counting_client.count_people_sync(
        videos_paths=[asset.asset_path for asset in assets]
    )
    assert all(
        are_detections_correct(
            detections=real_time_predictions.detections,
            up_amount=up_amount,
            down_amount=down_amount,
        )
        for real_time_predictions, up_amount, down_amount in zip(
            multiple_real_time_predictions, up_amounts, down_amounts
        )
    )
