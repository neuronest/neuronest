from __future__ import annotations

import argparse
import os

from core.google.storage_client import StorageClient
from core.path import GSPath
from core.schemas.image_name import ImageNameWithTag
from core.schemas.training_metrics.tables import TrainingMetrics
from core.services.training_metrics_writer import MetricsWriter
from core.utils import timeit
from google.cloud import bigquery
from omegaconf import DictConfig, OmegaConf

from object_detection.config import cfg
from object_detection.modules.model import ObjectDetectionModel


@timeit
def train_model(model_type: str, model_name: str) -> ObjectDetectionModel:
    return ObjectDetectionModel(
        model_type=model_type, model_name=model_name, retrieve_remote_model=True
    )


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
    model_directory: GSPath,
    image_name: ImageNameWithTag,
    config: DictConfig,
    args: argparse.Namespace,
):
    # noinspection PyArgumentList
    training_duration, model = train_model(
        model_type=config.model.inner_model_type,
        model_name=config.model.inner_model_name,
    )

    storage_client = StorageClient()

    model.save_on_gcs(storage_client=storage_client, directory_path=model_directory)

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
        bigquery_dataset_name=config.bigquery.dataset,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parsed_args = parser.parse_args()

    # defined in a Vertex AI environment:
    # https://cloud.google.com/vertex-ai/docs/training/code-requirements#environment-variables
    model_dir = os.getenv("AIP_MODEL_DIR")

    if model_dir is None:
        raise EnvironmentError(
            "The 'AIP_MODEL_DIR' environment variable is not defined, "
            "are we in a Vertex AI environment?"
        )

    image_name = os.getenv("IMAGE_NAME")

    if image_name is None:
        raise EnvironmentError("The 'IMAGE_NAME' environment variable is not defined")

    main(
        model_directory=GSPath(model_dir),
        image_name=ImageNameWithTag(image_name),
        config=cfg,
        args=parsed_args,
    )
