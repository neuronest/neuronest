from core.routes.base import _BaseRoutes


class _ServiceEvaluatorRoutes(_BaseRoutes):
    service_name: str = "service_evaluator"

    class Resources:
        prefix = "resources"
        region: str = "/region"
        firestore_jobs_collection: str = "/firestore_jobs_collection"
        bigquery_dataset_name: str = "/bigquery_dataset_name"

    class Evaluator:
        prefix = "evaluator"
        evaluate: str = "/evaluate"


routes: _ServiceEvaluatorRoutes = _ServiceEvaluatorRoutes()
