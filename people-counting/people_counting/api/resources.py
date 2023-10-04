from core.routes.people_counting import routes
from core.schemas.people_counting import (
    FirestoreResultsCollectionOutput,
    VideosToCountBucketOutput,
)
from fastapi import APIRouter
from starlette import status

from people_counting.environment_variables import (
    FIRESTORE_RESULTS_COLLECTION,
    VIDEOS_TO_COUNT_BUCKET,
)

router = APIRouter(prefix=f"/{routes.Resources.prefix}", tags=[routes.Resources.prefix])


@router.get(
    routes.Resources.videos_to_count_bucket,
    status_code=status.HTTP_200_OK,
)
def get_videos_to_count_bucket() -> VideosToCountBucketOutput:
    return VideosToCountBucketOutput(bucket=VIDEOS_TO_COUNT_BUCKET)


@router.get(
    routes.Resources.firestore_results_collection,
    status_code=status.HTTP_200_OK,
)
def get_firestore_results_collection() -> FirestoreResultsCollectionOutput:
    return FirestoreResultsCollectionOutput(collection=FIRESTORE_RESULTS_COLLECTION)
