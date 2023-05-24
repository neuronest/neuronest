from core.routes.base import _BaseRoutes


class _PeopleCountingRoutes(_BaseRoutes):
    service_name: str = "people_counting"
    count_people_and_make_video: str = "/count_people_and_make_video"


people_counting_routes: _PeopleCountingRoutes = _PeopleCountingRoutes()
