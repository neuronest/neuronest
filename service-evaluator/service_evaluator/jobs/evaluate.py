import json
from typing import Dict

from core.google.firestore_client import FirestoreClient
from core.schemas.service_evaluator import EvaluatedServiceName
from core.services.bigquery_writer import BigQueryWriter
from core.utils import string_to_boolean
from google.cloud import bigquery, bigquery_storage

from service_evaluator.config import cfg
from service_evaluator.dataset_manager import DatasetManager
from service_evaluator.jobs.environment_variables import (
    GOOGLE_APPLICATION_CREDENTIALS,
    PROJECT_ID,
    REGION,
    REUSE_ALREADY_COMPUTED_RESULTS,
    SERIALIZED_SERVICE_CLIENT_PARAMETERS,
    SERVICE_NAME,
)
from service_evaluator.predictor.factory import ServicePredictorFactory
from service_evaluator.results_handler import ResultsHandler
from service_evaluator.scorer.factory import ServiceScorerFactory


def make_firestore_client() -> FirestoreClient:
    return FirestoreClient(key_path=GOOGLE_APPLICATION_CREDENTIALS)


def make_service_client_parameters() -> Dict[str, str]:
    return json.loads(SERIALIZED_SERVICE_CLIENT_PARAMETERS)


def make_bigquery_client() -> bigquery.Client:
    return bigquery.Client(project=PROJECT_ID)


def make_bigquery_storage_client() -> bigquery_storage.BigQueryReadClient:
    if GOOGLE_APPLICATION_CREDENTIALS is None:
        return bigquery_storage.BigQueryReadClient()

    return bigquery_storage.BigQueryReadClient.from_service_account_json(
        GOOGLE_APPLICATION_CREDENTIALS
    )


def make_bigquery_writer(
    bigquery_client: bigquery.Client, bigquery_dataset_name: str
) -> BigQueryWriter:
    return BigQueryWriter(
        dataset_name=bigquery_dataset_name,
        big_query_client=bigquery_client,
        location=REGION,
    )


# TODO: decompose this function
# pylint: disable=too-many-locals
def main(
    service_name: EvaluatedServiceName,
    service_client_parameters: Dict[str, str],
    reuse_already_computed_results: bool,
    datasets_directory_name: str,
    dataset_filename: str,
    bigquery_dataset_name: str,
):
    bigquery_client = make_bigquery_client()
    bigquery_storage_client = make_bigquery_storage_client()
    bigquery_writer = make_bigquery_writer(
        bigquery_client=bigquery_client, bigquery_dataset_name=bigquery_dataset_name
    )
    results_handler = ResultsHandler(
        big_query_client=bigquery_client,
        bigquery_storage_client=bigquery_storage_client,
        bigquery_writer=bigquery_writer,
        service_name=service_name,
        big_query_dataset_name=bigquery_dataset_name,
        location=REGION,
    )

    service_predictor = ServicePredictorFactory.new(
        service_name=service_name,
        service_client_parameters=service_client_parameters,
    )
    service_scorer = ServiceScorerFactory.new(service_name=service_name)
    dataset_manager = DatasetManager.from_service_name(
        service_name=service_name,
        datasets_directory_name=datasets_directory_name,
        dataset_filename=dataset_filename,
    )
    dataset_manager.pull_dataset()

    service_image_name = service_predictor.client.get_underlying_serving_image(
        project_id=PROJECT_ID,
        location=REGION,
        key_path=GOOGLE_APPLICATION_CREDENTIALS,
    )

    already_computed_predictions = []
    if reuse_already_computed_results is True:
        already_computed_predictions = results_handler.read_existing_predictions(
            dataset_manager=dataset_manager,
            service_image_name=service_image_name,
            scorable_document_class=service_scorer.scorable_document_class,
        )

    if len(already_computed_predictions) == 0:
        predictions = service_predictor.run(dataset_manager=dataset_manager)
        prediction_documents = service_scorer.convert_predictions_to_scorable_documents(
            predictions=predictions
        )
    else:
        prediction_documents = already_computed_predictions

    real_documents = service_scorer.convert_dataset_to_scorable_documents(
        dataset=dataset_manager.dataset
    )

    scores = service_scorer.run(
        real_documents=real_documents, prediction_documents=prediction_documents
    )

    results_handler.write_predictions_and_scores(
        dataset_manager=dataset_manager,
        service_image_name=service_image_name,
        prediction_documents=prediction_documents,
        metric_name=service_scorer.metric.name,
        scores=scores,
    )


if __name__ == "__main__":
    main(
        service_name=EvaluatedServiceName(SERVICE_NAME),
        service_client_parameters=make_service_client_parameters(),
        reuse_already_computed_results=string_to_boolean(
            REUSE_ALREADY_COMPUTED_RESULTS
        ),
        datasets_directory_name=cfg.paths.datasets_directory_name,
        dataset_filename=cfg.paths.dataset_filename,
        bigquery_dataset_name=cfg.bigquery.dataset.name,
    )
