import json
from typing import Dict

from core.google.firestore_client import FirestoreClient
from core.schemas.service_evaluator import EvaluatedServiceName
from core.services.bigquery_writer import BigQueryWriter
from google.cloud import bigquery, bigquery_storage
from omegaconf import DictConfig

from service_evaluator.config import cfg
from service_evaluator.dataset_manager import DatasetManager
from service_evaluator.jobs.environment_variables import (
    GOOGLE_APPLICATION_CREDENTIALS,
    PROJECT_ID,
    REGION,
    SERIALIZED_SERVICE_CLIENT_PARAMETERS,
    SERVICE_NAME,
)
from service_evaluator.predictor.factory import ServicePredictorFactory
from service_evaluator.results_writer import ResultsWriter
from service_evaluator.scorer.factory import ServiceScorerFactory


def make_firestore_client() -> FirestoreClient:
    return FirestoreClient(key_path=GOOGLE_APPLICATION_CREDENTIALS)


def make_service_client_parameters() -> Dict[str, str]:
    return json.loads(SERIALIZED_SERVICE_CLIENT_PARAMETERS)


def make_bigquery_client() -> bigquery.Client:
    return bigquery.Client(project=PROJECT_ID)


def make_bigquery_storage_client() -> bigquery_storage.BigQueryReadClient:
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


def main(
    config: DictConfig,
    service_name: EvaluatedServiceName,
    service_client_parameters: Dict[str, str],
):
    datasets_directory_name = config.paths.datasets_directory_name
    dataset_filename = config.paths.dataset_filename
    bigquery_dataset_name = config.bigquery.dataset.name

    bigquery_client = make_bigquery_client()
    bigquery_storage_client = make_bigquery_storage_client()
    bigquery_writer = make_bigquery_writer(
        bigquery_client=bigquery_client, bigquery_dataset_name=bigquery_dataset_name
    )
    results_writer = ResultsWriter(
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

    predictions = service_predictor.run(dataset_manager=dataset_manager)
    scores = service_scorer.run(
        dataset_manager=dataset_manager, predictions=predictions
    )

    results_writer.submit(dataset_manager=dataset_manager, scores=scores)


if __name__ == "__main__":
    main(
        config=cfg,
        service_name=SERVICE_NAME,
        service_client_parameters=make_service_client_parameters(),
    )
