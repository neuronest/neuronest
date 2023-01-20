from __future__ import annotations

import argparse
import logging
from enum import Enum
from typing import List, Optional

from core.google.storage_client import StorageClient
from core.google.vertex_ai_manager import VertexAIManager
from core.path import GSPath
from core.schemas.vertex_ai import (
    ServingDeploymentConfig,
    ServingModelUploadConfig,
    TrainingConfig,
)
from google.cloud import aiplatform
from omegaconf import DictConfig

from object_detection.config import cfg
from object_detection.environment_variables import (
    GOOGLE_APPLICATION_CREDENTIALS,
    TRAINING_IMAGE_NAME,
)

logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)


class Mode(str, Enum):
    TRAIN = "train"
    MODEL_UPLOAD = "model_upload"
    REMOVE_LAST_MODEL_VERSION = "remove_last_model_version"
    DEPLOY = "deploy"
    UNDEPLOY = "undeploy"

    @classmethod
    def training_modes(cls) -> List[Mode]:
        return [cls.TRAIN]

    @classmethod
    def serving_modes(cls) -> List[Mode]:
        return [mode for mode in map(cls, Mode) if not mode.is_training_mode]

    @property
    def is_training_mode(self) -> bool:
        return self in self.training_modes()

    @property
    def is_serving_mode(self) -> bool:
        return self in self.serving_modes()


def launch_training_job(
    model_gspath: GSPath,
    project_id: str,
    model_name: str,
    region: str,
    container_uri: str,
    machine_type: str,
    accelerator_type: str,
    accelerator_count: int,
    replica_count: int,
):
    models_bucket_name, _ = model_gspath.to_bucket_and_blob_names()
    StorageClient().create_bucket(
        bucket_name=models_bucket_name, location=region, exist_ok=True
    )

    # unspecified: it won't produce a Vertex Model because no
    # model_serving_container_image_uri is specified (a custom one will be created)
    model_display_name = None

    training_job = aiplatform.CustomContainerTrainingJob(
        display_name=model_name,
        location=region,
        staging_bucket=models_bucket_name,
        container_uri=container_uri,
        command=["python3", "-m", f"{model_name}.train"],
    )

    # will raise a RuntimeError if the job itself crashed
    training_job.run(
        model_display_name=model_display_name,
        replica_count=replica_count,
        machine_type=machine_type,
        accelerator_type=accelerator_type,
        accelerator_count=accelerator_count,
        base_output_dir=model_gspath,
        environment_variables={
            "IMAGE_NAME": TRAINING_IMAGE_NAME,
            "PROJECT_ID": project_id,
            "REGION": region,
        },
    )


def train(
    training_config: TrainingConfig,
    vertex_ai_manager: VertexAIManager,
    model_name: str,
    model_gspath: GSPath,
):
    launch_training_job(
        model_gspath=model_gspath,
        project_id=vertex_ai_manager.project_id,
        model_name=model_name,
        region=vertex_ai_manager.location,
        container_uri=training_config.container_uri,
        machine_type=training_config.machine_type,
        replica_count=training_config.replica_count,
        accelerator_type=training_config.accelerator_type,
        accelerator_count=training_config.accelerator_count,
    )


def upload_model(
    serving_model_upload_config: ServingModelUploadConfig,
    serving_deployment_config: ServingDeploymentConfig,
    vertex_ai_manager: VertexAIManager,
    model_name: str,
) -> aiplatform.Model:
    return vertex_ai_manager.upload_model(
        name=model_name,
        serving_model_upload_config=serving_model_upload_config,
        serving_deployment_config=serving_deployment_config,
    )


def deploy(
    vertex_ai_manager: VertexAIManager,
    model_name: str,
):
    model = vertex_ai_manager.get_model_by_name(name=model_name)

    if model is None:
        raise ValueError(f"No model found with name: {model_name}")

    model_labels = model.labels

    if model_labels is None:
        raise ValueError(f"No labels found in the model with name: {model_name}")

    serving_deployment_config = ServingDeploymentConfig.parse_obj(model_labels)

    vertex_ai_manager.deploy_model(
        name=model_name,
        model=model,
        serving_deployment_config=serving_deployment_config,
        undeploy_previous_model=True,
    )


def remove_last_model_version(vertex_ai_manager: VertexAIManager, model_name: str):
    model = vertex_ai_manager.get_model_by_name(name=model_name)

    if model is None:
        return

    model_registry = model.versioning_registry

    all_model_versions = model_registry.list_versions()

    if len(all_model_versions) == 0:
        return

    if len(all_model_versions) == 1:
        vertex_ai_manager.delete_model_by_name(name=model_name)

    sorted_model_versions = sorted(
        all_model_versions,
        key=lambda version: version.version_create_time,
        reverse=True,
    )
    last_model_version, before_last_model_version = sorted_model_versions[:2]

    if model.version_id != last_model_version.version_id:
        raise ValueError(
            f"Recovered default model and last model don't have the same version "
            f"({model.version_id} != {last_model_version})"
        )

    version_aliases = list(model.version_aliases)
    model_registry.add_version_aliases(
        version=before_last_model_version.version_id, new_aliases=version_aliases
    )
    model_registry.delete_version(last_model_version.version_id)


def undeploy(vertex_ai_manager: VertexAIManager, model_name: str):
    return vertex_ai_manager.delete_endpoint(name=model_name, undeploy_models=True)


def main(config: DictConfig, model_gspath: Optional[GSPath], modes: List[Mode]):
    vertex_ai_manager = VertexAIManager(
        key_path=GOOGLE_APPLICATION_CREDENTIALS, location=config.region
    )
    model_name = config.model.name

    if len(modes) == 0:
        raise ValueError("No mode received")

    if Mode.TRAIN in modes:
        training_config = TrainingConfig(**config.training)

        if model_gspath is None:
            raise ValueError(
                "model_gspath parameter should be specified in training mode"
            )

        train(
            training_config=training_config,
            vertex_ai_manager=vertex_ai_manager,
            model_name=model_name,
            model_gspath=model_gspath,
        )

    if not any(mode.is_serving_mode for mode in modes):
        return

    if Mode.MODEL_UPLOAD in modes:
        serving_model_upload_config = ServingModelUploadConfig(
            **config.serving_model_upload
        )
        serving_deployment_config = ServingDeploymentConfig(**config.serving_deployment)

        upload_model(
            serving_model_upload_config=serving_model_upload_config,
            serving_deployment_config=serving_deployment_config,
            vertex_ai_manager=vertex_ai_manager,
            model_name=model_name,
        )

    if Mode.DEPLOY in modes:
        deploy(
            vertex_ai_manager=vertex_ai_manager,
            model_name=model_name,
        )

    if Mode.UNDEPLOY in modes:
        undeploy(
            vertex_ai_manager=vertex_ai_manager,
            model_name=model_name,
        )

    if Mode.REMOVE_LAST_MODEL_VERSION in modes:
        remove_last_model_version(
            vertex_ai_manager=vertex_ai_manager, model_name=model_name
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-gspath", dest="model_gspath")
    parser.add_argument(
        "--modes",
        dest="modes",
        choices=list(Mode),
        nargs="+",
    )

    parsed_args = parser.parse_args()

    main(
        config=cfg,
        model_gspath=None
        if parsed_args.model_gspath is None
        else GSPath(parsed_args.model_gspath),
        modes=[Mode(mode) for mode in parsed_args.modes],
    )
