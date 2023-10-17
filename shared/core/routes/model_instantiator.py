from core.routes.base import _BaseRoutes


class _ModelInstantiatorRoutes(_BaseRoutes):
    service_name: str = "model_instantiator"

    class Instantiator:
        prefix = "instantiator"
        instantiate: str = "/instantiate"

    class Uninstantiator:
        prefix = "uninstantiator"
        uninstantiate: str = "/uninstantiate"
        uninstantiate_logs_conditioned: str = "/uninstantiate_logs_conditioned"


routes: _ModelInstantiatorRoutes = _ModelInstantiatorRoutes()
