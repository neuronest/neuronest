import os
from typing import List, Optional

from core.client.abstract.prediction_api_client import make_results_blob_name
from core.path import GSPath
from core.schemas.modules.people_counting import PeopleCounterSampleResultsDocument
from core.services.asset_reader import make_asset
from joblib import Parallel, delayed

from people_counting.config import config as cfg
from people_counting.jobs.environment_variables import (
    COUNTED_VIDEOS_STORAGE_PATHS,
    JOB_ID,
    MODEL_INSTANTIATOR_HOST,
    OBJECT_DETECTION_MODEL_NAME,
    PROJECT_ID,
    REGION,
    RESULTS_BUCKET,
    VIDEOS_STORAGE_PATHS,
)
from people_counting.jobs.services import create_people_counter, create_storage_client
from people_counting.people_counter import count_people_with_upload


def run_asset_counting(
    video_storage_path: GSPath,
    counted_video_storage_path: Optional[GSPath],
    project_id: str,
    region: str,
    job_id: str,
    object_detection_model_name: str,
    model_instantiator_host: str,
    results_bucket: str,
):
    storage_client = create_storage_client(project_id=project_id)
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
    asset_id = video_asset.get_hash()

    statistics = count_people_with_upload(
        people_counter=people_counter,
        storage_client=storage_client,
        video_asset=video_asset,
        counted_video_storage_path=counted_video_storage_path,
    )

    people_counter_document = PeopleCounterSampleResultsDocument(
        sample_id=asset_id,
        job_id=job_id,
        detections=statistics.to_detections(),
        video_storage_path=video_storage_path,
        counted_video_storage_path=counted_video_storage_path,
    )

    storage_client.upload_blob_from_dict(
        bucket_name=results_bucket,
        blob_name=make_results_blob_name(job_id=job_id, sample_id=asset_id),
        content=people_counter_document.dict(),
    )


def main(
    project_id: str,
    region: str,
    object_detection_model_name: str,
    model_instantiator_host: str,
    results_bucket: str,
    job_id: str,
    videos_storage_paths: List[str],
    counted_videos_storage_paths: Optional[List[str]],
):
    if counted_videos_storage_paths is not None:
        if len(videos_storage_paths) != len(counted_videos_storage_paths):
            raise ValueError(
                "If counted_videos_storage_paths is specified, its length should be "
                "the same as videos_storage_paths"
            )
    else:
        counted_videos_storage_paths = [None] * len(videos_storage_paths)

    return Parallel(n_jobs=os.cpu_count())(
        delayed(run_asset_counting)(
            video_storage_path=GSPath(video_storage_path),
            counted_video_storage_path=GSPath(counted_video_storage_path)
            if counted_video_storage_path is not None
            else None,
            project_id=project_id,
            region=region,
            job_id=job_id,
            object_detection_model_name=object_detection_model_name,
            model_instantiator_host=model_instantiator_host,
            results_bucket=results_bucket,
        )
        for video_storage_path, counted_video_storage_path in zip(
            videos_storage_paths, counted_videos_storage_paths
        )
    )


if __name__ == "__main__":
    main(
        project_id=PROJECT_ID,
        region=REGION,
        object_detection_model_name=OBJECT_DETECTION_MODEL_NAME,
        model_instantiator_host=MODEL_INSTANTIATOR_HOST,
        results_bucket=RESULTS_BUCKET,
        job_id=JOB_ID,
        videos_storage_paths=VIDEOS_STORAGE_PATHS,
        counted_videos_storage_paths=COUNTED_VIDEOS_STORAGE_PATHS,
    )
