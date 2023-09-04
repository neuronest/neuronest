import tempfile
from typing import Optional

from core.google.storage_client import StorageClient
from core.path import GSPath
from core.schemas.asset import VideoAssetContent
from core.schemas.people_counting import PeopleCounterDocument
from core.services.asset_reader import make_asset_content
from core.tools import extract_file_extension

from people_counting.common import Statistics
from people_counting.config import config as cfg
from people_counting.jobs.environment_variables import (
    ASSET_ID,
    COUNTED_VIDEO_STORAGE_PATH,
    FIRESTORE_RESULTS_COLLECTION,
    JOB_ID,
    MODEL_INSTANTIATOR_HOST,
    OBJECT_DETECTION_MODEL_NAME,
    PROJECT_ID,
    REGION,
    VIDEO_STORAGE_PATH,
)
from people_counting.jobs.services import (
    create_firestore_client,
    create_people_counter,
    create_storage_client,
)
from people_counting.people_counter import PeopleCounter


def count_people(
    people_counter: PeopleCounter,
    storage_client: StorageClient,
    video_asset_content: VideoAssetContent,
    counted_video_storage_path: Optional[GSPath],
) -> Statistics:
    if counted_video_storage_path is not None:
        extension = extract_file_extension(video_asset_content.asset_path)

        (
            counted_videos_bucket,
            counted_videos_blob_name,
        ) = counted_video_storage_path.to_bucket_and_blob_names()

        with tempfile.NamedTemporaryFile(suffix=extension) as named_temporary_file:
            statistics = people_counter.run(
                video_asset_content=video_asset_content,
                video_output_path=named_temporary_file.name,
            )

            storage_client.upload_blob(
                source_file_name=named_temporary_file.name,
                bucket_name=counted_videos_bucket,
                blob_name=counted_videos_blob_name,
            )

            return statistics

    statistics, _ = people_counter.run(
        video_asset_content=video_asset_content,
    )

    return statistics


def main(
    job_id: str,
    asset_id: str,
    video_storage_path: GSPath,
    firestore_results_collection: str,
    counted_video_storage_path: Optional[GSPath],
):
    storage_client = create_storage_client()
    firestore_client = create_firestore_client()
    people_counter = create_people_counter(
        project_id=PROJECT_ID,
        region=REGION,
        model_instantiator_host=MODEL_INSTANTIATOR_HOST,
        object_detection_model_name=OBJECT_DETECTION_MODEL_NAME,
        config=cfg,
    )

    video_asset_content = make_asset_content(
        asset_path=video_storage_path, storage_client=storage_client
    )

    statistics = count_people(
        people_counter=people_counter,
        storage_client=storage_client,
        video_asset_content=video_asset_content,
        counted_video_storage_path=counted_video_storage_path,
    )

    people_counter_document = PeopleCounterDocument(
        job_id=job_id,
        asset_id=asset_id,
        storage_path=video_storage_path,
        detections=statistics.to_detections(),
    )

    firestore_client.upload_document(
        collection_name=firestore_results_collection,
        document_id=job_id,
        content=people_counter_document.dict(),
    )


if __name__ == "__main__":
    main(
        job_id=JOB_ID,
        asset_id=ASSET_ID,
        video_storage_path=VIDEO_STORAGE_PATH,
        firestore_results_collection=FIRESTORE_RESULTS_COLLECTION,
        counted_video_storage_path=COUNTED_VIDEO_STORAGE_PATH,
    )
