from core.routes.base import BaseResources, _BaseRoutes


class _PeopleCountingRoutes(_BaseRoutes):
    service_name: str = "people_counting"

    class Resources(BaseResources):
        videos_to_count_bucket: str = "/videos_to_count_bucket"
        maximum_videos_number: str = "/maximum_videos_number"

    class PeopleCounter:
        prefix = "people_counter"
        count_people: str = "/count_people"
        count_people_real_time: str = "/count_people_real_time"


routes: _PeopleCountingRoutes = _PeopleCountingRoutes()
