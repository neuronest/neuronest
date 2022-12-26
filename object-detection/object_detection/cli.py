import argparse
import logging
from enum import Enum

from core.google.storage_client import StorageClient
from core.google.vertex_ai_manager import ServingConfig, TrainingConfig, VertexAIManager
from core.path import GSPath
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
    TRAINING = "training"
    MODEL_UPLOADING = "model_uploading"
    SERVING = "serving"


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
        accelerator_type=training_config.accelerator_type,
        accelerator_count=training_config.accelerator_count,
        replica_count=training_config.replica_count,
    )


def upload_model(
    serving_config: ServingConfig, vertex_ai_manager: VertexAIManager, model_name: str
) -> aiplatform.Model:
    return vertex_ai_manager.upload_model(
        name=model_name, serving_config=serving_config
    )


def serve(
    serving_config: ServingConfig, vertex_ai_manager: VertexAIManager, model_name: str
):
    model = vertex_ai_manager.get_last_model_by_name(name=model_name)

    if model is None:
        raise ValueError(f"No model found with name: {model_name}")

    vertex_ai_manager.deploy_model(
        name=model_name, model=model, serving_config=serving_config
    )


def main(config: DictConfig, parsed_args: argparse.Namespace):
    vertex_ai_manager = VertexAIManager(
        key_path=GOOGLE_APPLICATION_CREDENTIALS, location=config.region
    )
    model_name = config.model.name

    if parsed_args.mode == Mode.TRAINING:
        training_config = TrainingConfig(**config.training_spec)

        if parsed_args.model_gspath is None:
            raise ValueError(
                "model_gspath parameter should be specified in training mode"
            )

        return train(
            training_config=training_config,
            vertex_ai_manager=vertex_ai_manager,
            model_name=model_name,
            model_gspath=GSPath(parsed_args.model_gspath),
        )

    serving_config = ServingConfig(**config.serving_spec)

    if parsed_args.mode == Mode.MODEL_UPLOADING:
        return upload_model(
            serving_config=serving_config,
            vertex_ai_manager=vertex_ai_manager,
            model_name=model_name,
        )

    if parsed_args.mode == Mode.SERVING:
        return serve(
            serving_config=serving_config,
            vertex_ai_manager=vertex_ai_manager,
            model_name=model_name,
        )

    raise ValueError(f"Unsupported mode: {parsed_args.mode}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-gspath", dest="model_gspath")
    parser.add_argument(
        "--overwrite-endpoint",
        action="store_true",
        dest="overwrite_endpoint",
        default=True,
    )
    parser.add_argument(
        "--mode", dest="mode", choices=["training", "model_uploading", "serving"]
    )

    main(config=cfg, parsed_args=parser.parse_args())
