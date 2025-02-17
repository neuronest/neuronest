from core.client.service_evaluator import ServiceEvaluatorClient
from core.schemas.service_evaluator import EvaluateResultsDocument


# pylint: disable=unused-argument
def test_count_people_sync(
    service_evaluator_client: ServiceEvaluatorClient,
    uninstantiate_teardown,
):
    evaluate_results_document = service_evaluator_client.evaluate_sync()

    assert isinstance(evaluate_results_document, EvaluateResultsDocument)
