from core.routes.base import _BaseRoutes


class _PeopleCountingRoutes(_BaseRoutes):
    service_name: str = "people_counting"

    class PeopleCounter:
        prefix = "people_counter"
        count_people_and_make_video: str = "/count_people_and_make_video"


routes: _PeopleCountingRoutes = _PeopleCountingRoutes()
