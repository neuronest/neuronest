from typing import List

import pytest
from core.client.people_counting import PeopleCountingClient
from core.google.storage_client import StorageClient
from core.path import GSPath
from core.schemas.asset import AssetType
from core.schemas.people_counting import PeopleCounterAssetResultsDocument
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
@pytest.mark.order(1)
def test_count_people_cloud_job(
    people_counting_client: PeopleCountingClient,
    storage_client: StorageClient,
    videos_storage_paths: List[GSPath],
    up_amounts: List[int],
    down_amounts: List[int],
):
    assets = make_assets(
        assets_paths=videos_storage_paths,
        asset_type=AssetType.VIDEO,
        storage_client=storage_client,
    )

    people_counter_outputs = people_counting_client.count_people(
        videos_paths=[asset.asset_path for asset in assets],
    )
    people_counter_job_results_documents = [
        people_counting_client.get_predictions_from_job_id(
            job_id=people_counter_output.job_id, wait_if_not_existing=True
        )
        for people_counter_output in people_counter_outputs
    ]
    all_assets_results: List[PeopleCounterAssetResultsDocument] = [
        asset_results
        for people_counter_job_results_document in people_counter_job_results_documents
        for asset_results in people_counter_job_results_document.results
    ]

    assert all(
        people_counter_asset_results_document.job_id == people_counter_output.job_id
        for people_counter_job_results_document, people_counter_output in zip(
            people_counter_job_results_documents, people_counter_outputs
        )
        for people_counter_asset_results_document in (
            people_counter_job_results_document.results
        )
    )
    assert all(
        are_detections_correct(
            detections=asset_results.detections,
            up_amount=up_amount,
            down_amount=down_amount,
        )
        for asset_results, up_amount, down_amount in zip(
            all_assets_results, up_amounts, down_amounts
        )
    )
