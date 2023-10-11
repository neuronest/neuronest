from core.routes.base import _BaseRoutes


class _PeopleCountingRoutes(_BaseRoutes):
    service_name: str = "people_counting"

    class Resources:
        prefix = "resources"
        videos_to_count_bucket: str = "/videos_to_count_bucket"
        firestore_results_collection: str = "/firestore_results_collection"
        firestore_jobs_collection: str = "/firestore_jobs_collection"
        maximum_videos_number: str = "/maximum_videos_number"

    class PeopleCounter:
        prefix = "people_counter"
        count_people: str = "/count_people"
        count_people_real_time: str = "/count_people_real_time"


routes: _PeopleCountingRoutes = _PeopleCountingRoutes()
