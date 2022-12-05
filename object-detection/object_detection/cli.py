import argparse
import logging
from datetime import datetime
from typing import Optional, Union

from core.google.storage_client import StorageClient
from core.path import GSPath
from google.cloud import aiplatform
from omegaconf import DictConfig

from object_detection.config import cfg
from object_detection.environment_variables import IMAGE_NAME

logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)


def launch_training_job(
    models_bucket_name: str,
    model_name: str,
    location: str,
    training_container_uri: str,
    training_machine_type: str,
    accelerator_type: str,
    accelerator_count: int,
    serving_container_uri: Optional[str] = None,
) -> Union[str, GSPath]:
    StorageClient().create_bucket(
        bucket_name=models_bucket_name, location=location, exist_ok=True
    )

    will_produce_model = serving_container_uri is not None

    artifacts_path = None
    if will_produce_model is False:
        timestamp = datetime.now().isoformat(sep="-", timespec="milliseconds")
        artifacts_path = GSPath.from_bucket_and_blob_names(
            models_bucket_name, "-".join([model_name, timestamp])
        )

    job = aiplatform.CustomContainerTrainingJob(
        display_name=model_name,
        location=location,
        staging_bucket=models_bucket_name,
        container_uri=training_container_uri,
        model_serving_container_image_uri=serving_container_uri,
        command=["python3", "-m", f"{model_name}.train"],
    ).run(
        model_display_name=model_name if will_produce_model is True else None,
        replica_count=1,  # fixed to 1, we absolutely do not need distributing training
        machine_type=training_machine_type,
        accelerator_type=accelerator_type,
        accelerator_count=accelerator_count,
        base_output_dir=artifacts_path,
        environment_variables={"IMAGE_NAME": IMAGE_NAME},
    )

    if will_produce_model is True:
        return job.name

    return artifacts_path


def main(
    overwrite_endpoint: bool,
    config: DictConfig,
):

    artifacts_path = launch_training_job(
        models_bucket_name=config.storage.models_bucket_name,
        model_name=config.model.name,
        location=config.region,
        training_container_uri=config.model_infra.training_container_uri,
        training_machine_type=config.model_infra.training_machine_type,
        accelerator_type=config.model_infra.training_accelerator_type,
        accelerator_count=config.model_infra.training_accelerator_count,
    )

    return artifacts_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--overwrite-endpoint",
        action="store_true",
        dest="overwrite_endpoint",
        default=True,
    )

    args = parser.parse_args()
    main(overwrite_endpoint=args.overwrite_endpoint, config=cfg)
