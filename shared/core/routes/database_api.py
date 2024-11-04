from core.routes.base import _BaseRoutes


class _DatabaseApiRoutes(_BaseRoutes):
    service_name: str = "database_api"

    class Project:
        prefix = "project"
        create: str = "/create"

    class Uninstantiator:
        prefix = "uninstantiator"
        uninstantiate: str = "/uninstantiate"
        uninstantiate_logs_conditioned: str = "/uninstantiate_logs_conditioned"


routes: _DatabaseApiRoutes = _DatabaseApiRoutes()
