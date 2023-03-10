from core.routes.base import _BaseRoutes


class _ModelInstantiatorRoutes(_BaseRoutes):
    service_name: str = "model_instantiator"
    instantiate: str = "/instantiate"
    uninstantiate: str = "/uninstantiate"
    uninstantiate_logs_conditioned: str = "/uninstantiate_logs_conditioned"


route: _ModelInstantiatorRoutes = _ModelInstantiatorRoutes()
