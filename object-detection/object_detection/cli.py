import argparse
import logging
from enum import Enum

from core.google.storage_client import StorageClient
from core.path import GSPath
from google.cloud import aiplatform
from omegaconf import DictConfig

from object_detection.config import cfg
from object_detection.environment_variables import TRAINING_IMAGE_NAME

logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)


class Mode(str, Enum):
    TRAINING = "training"
    SERVING = "serving"


def launch_training_job(
    model_gspath: GSPath,
    project_id: str,
    models_bucket_name: str,
    model_name: str,
    region: str,
    training_container_uri: str,
    training_machine_type: str,
    accelerator_type: str,
    accelerator_count: int,
):
    StorageClient().create_bucket(
        bucket_name=models_bucket_name, location=region, exist_ok=True
    )

    # unspecified: it won't produce a Vertex Model because no
    # model_serving_container_image_uri is specified (a custom one will be created)
    model_display_name = None
    replica_count = 1  # fixed to 1, we do not need distributing training

    training_job = aiplatform.CustomContainerTrainingJob(
        display_name=model_name,
        location=region,
        staging_bucket=models_bucket_name,
        container_uri=training_container_uri,
        command=["python3", "-m", f"{model_name}.train"],
    )

    # will raise a RuntimeError if the job itself crashed
    training_job.run(
        model_display_name=model_display_name,
        replica_count=replica_count,
        machine_type=training_machine_type,
        accelerator_type=accelerator_type,
        accelerator_count=accelerator_count,
        base_output_dir=model_gspath,
        environment_variables={
            "IMAGE_NAME": TRAINING_IMAGE_NAME,
            "PROJECT_ID": project_id,
            "REGION": region,
        },
    )


def train(config: DictConfig, model_gspath: GSPath):
    launch_training_job(
        model_gspath=model_gspath,
        project_id=config.project_id,
        models_bucket_name=config.storage.models_bucket_name,
        model_name=config.model.name,
        region=config.region,
        training_container_uri=config.model_infra.training_container_uri,
        training_machine_type=config.model_infra.training_machine_type,
        accelerator_type=config.model_infra.training_accelerator_type,
        accelerator_count=config.model_infra.training_accelerator_count,
    )


def serve():
    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-gspath", dest="model_gspath", required=True)
    parser.add_argument(
        "--overwrite-endpoint",
        action="store_true",
        dest="overwrite_endpoint",
        default=True,
    )
    parser.add_argument("--mode", dest="mode", choices=["training", "serving"])

    args = parser.parse_args()

    if args.mode == Mode.TRAINING:
        train(config=cfg, model_gspath=GSPath(args.model_gspath))
