from __future__ import annotations

import os

from google.cloud import bigquery
from omegaconf import DictConfig, OmegaConf

from core.google.storage_client import StorageClient
from core.packages.abstract.online_prediction_model.modules.model import (
    OnlinePredictionModel,
)
from core.path import GSPath
from core.schemas.image_name import ImageNameWithTag
from core.schemas.training_metrics.tables import TrainingMetrics
from core.services.training_metrics_writer import MetricsWriter
from core.utils import timeit


@timeit
def train_model(
    online_prediction_model: OnlinePredictionModel, *args, **kwargs
) -> OnlinePredictionModel:
    # def train_model(model_type: str, model_name: str) -> ObjectDetectionModel:
    online_prediction_model.fit(*args, **kwargs)
    return online_prediction_model
    # return ObjectDetectionModel(
    #     model_type=model_type, model_name=model_name, retrieve_remote_model=True
    # )


def write_metrics(
    training_metrics: TrainingMetrics,
    project_id: str,
    location: str,
    bigquery_dataset_name: str,
):
    # noinspection PyTypeChecker
    bigquery_client = bigquery.Client(project=project_id)

    MetricsWriter(
        dataset_name=bigquery_dataset_name,
        big_query_client=bigquery_client,
        location=location,
    ).submit(training_metrics)


def main(
    online_prediction_model,
    config: DictConfig,
    *online_prediction_model_training_args,
    **online_prediction_model_training_kwargs,
):
    # defined in a Vertex AI environment:
    # https://cloud.google.com/vertex-ai/docs/training/code-requirements#environment-variables
    if os.getenv("AIP_MODEL_DIR") is None:
        raise EnvironmentError(
            "The 'AIP_MODEL_DIR' environment variable is not defined, "
            "are we in a Vertex AI environment?"
        )
    model_directory = GSPath(os.getenv("AIP_MODEL_DIR"))

    # pylint: disable=unpacking-non-sequence
    # noinspection PyArgumentList
    # training_duration, model = train_model(
    #     model_type=config.model.inner_model_type,
    #     model_name=config.model.inner_model_name,
    # )
    training_duration, online_prediction_model = train_model(
        online_prediction_model=online_prediction_model,
        *online_prediction_model_training_args,
        **online_prediction_model_training_kwargs,
    )

    storage_client = StorageClient()

    online_prediction_model.save_on_gcs(
        storage_client=storage_client, directory_path=model_directory
    )

    image_name = ImageNameWithTag(os.environ["IMAGE_NAME"])
    training_metrics = TrainingMetrics(
        model_name=config.model.name,
        training_duration=training_duration,
        metrics={},
        parameters=OmegaConf.to_container(config),
        model_path=model_directory,
        image_name=image_name,
    )

    write_metrics(
        training_metrics=training_metrics,
        project_id=config.project_id,
        location=config.region,
        bigquery_dataset_name=config.bigquery.dataset.name,
    )


if __name__ == "__main__":
    cfg = None  # pylint: disable=invalid-name
    model = None  # pylint: disable=invalid-name
    training_args = ()  # pylint: disable=invalid-name
    training_kwargs = {}  # pylint: disable=invalid-name
    # we encapsulate 100 % of the logic in a single function to be imported and reused
    # in specialized repositories and we delegate to those repositories the only things
    # that are not known in advance:
    # the config, the instantiation of the model and the training arguments
    main(online_prediction_model=model, config=cfg, *training_args, **training_kwargs)
