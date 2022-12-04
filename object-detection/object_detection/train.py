from __future__ import annotations

import argparse
import os

from google.cloud import bigquery
from model.config import cfg
from modules.model import ObjectDetectionModel
from omegaconf import DictConfig, OmegaConf
from core.google.storage_client import StorageClient
from core.path import GSPath
from core.schemas.image_name import ImageNameWithTag
from core.schemas.training_metrics.tables import TrainingMetrics
from core.services.training_metrics_writer import MetricsWriter
from core.utils import timeit


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
    analysis_image_name: ImageNameWithTag,
    config: DictConfig,
    args: argparse.Namespace,
):
    # noinspection PyArgumentList
    training_duration, model = train_model(
        model_type=config.inner_model_type, model_name=config.inner_model_name
    )

    storage_client = StorageClient()

    model.save(storage_client=storage_client, directory_path=model_directory)

    training_metrics = TrainingMetrics(
        model_name=config.model_name,
        training_duration=training_duration,
        metrics={},
        parameters=OmegaConf.to_container(config),
        model_path=model_directory,
        analysis_image_name=analysis_image_name,
    )

    write_metrics(
        training_metrics=training_metrics,
        project_id=config.gcp_project_id,
        location=config.location,
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

    package_image_name = os.getenv("PACKAGE_IMAGE_NAME")

    if package_image_name is None:
        raise EnvironmentError(
            "The 'PACKAGE_IMAGE_NAME' environment variable is not defined"
        )

    main(
        model_directory=GSPath(model_dir),
        analysis_image_name=ImageNameWithTag(package_image_name),
        config=cfg,
        args=parsed_args,
    )
