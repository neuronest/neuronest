from core.routes.base import _BaseRoutes


class _PeopleCountingRoutes(_BaseRoutes):
    service_name: str = "people_counting"
    count_people: str = "/count_people"
    count_people_real_time_showing: str = "/count_people_real_time_showing"


routes: _PeopleCountingRoutes = _PeopleCountingRoutes()
