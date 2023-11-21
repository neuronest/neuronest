from core.routes.base import _BaseRoutes


class _ServiceEvaluatorRoutes(_BaseRoutes):
    service_name: str = "service_evaluator"

    class Evaluator:
        prefix = "evaluator"
        evaluate: str = "/evaluate"


routes: _ServiceEvaluatorRoutes = _ServiceEvaluatorRoutes()
