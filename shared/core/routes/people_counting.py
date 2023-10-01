from core.routes.base import _BaseRoutes


class _PeopleCountingRoutes(_BaseRoutes):
    service_name: str = "people_counting"

    class PeopleCounter:
        prefix = "people_counter"
        videos_to_count_bucket: str = "/videos_to_count_bucket"
        count_people: str = "/count_people"
        count_people_real_time: str = "/count_people_real_time"


routes: _PeopleCountingRoutes = _PeopleCountingRoutes()
