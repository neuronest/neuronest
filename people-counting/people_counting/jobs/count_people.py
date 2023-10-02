from typing import Optional

from core.schemas.people_counting import PeopleCounterDocument
from core.services.asset_reader import make_asset

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
from people_counting.people_counter import count_people_with_upload


def main(
    project_id: str,
    region: str,
    object_detection_model_name: str,
    model_instantiator_host: str,
    firestore_results_collection: str,
    job_id: str,
    asset_id: str,
    video_storage_path: str,
    counted_video_storage_path: Optional[str],
):
    storage_client = create_storage_client()
    firestore_client = create_firestore_client()
    people_counter = create_people_counter(
        project_id=project_id,
        region=region,
        model_instantiator_host=model_instantiator_host,
        object_detection_model_name=object_detection_model_name,
        config=cfg,
    )

    video_asset = make_asset(
        asset_path=video_storage_path, storage_client=storage_client
    )

    statistics = count_people_with_upload(
        people_counter=people_counter,
        storage_client=storage_client,
        video_asset=video_asset,
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
        project_id=PROJECT_ID,
        region=REGION,
        object_detection_model_name=OBJECT_DETECTION_MODEL_NAME,
        model_instantiator_host=MODEL_INSTANTIATOR_HOST,
        firestore_results_collection=FIRESTORE_RESULTS_COLLECTION,
        job_id=JOB_ID,
        asset_id=ASSET_ID,
        video_storage_path=VIDEO_STORAGE_PATH,
        counted_video_storage_path=COUNTED_VIDEO_STORAGE_PATH,
    )
