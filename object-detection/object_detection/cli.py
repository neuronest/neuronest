import argparse
import logging
from typing import Optional

from core.schemas.image_name import ImageNameWithTag
from omegaconf import DictConfig

from object_detection.config import cfg

logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)


def generate_cloud_build_command(
    region: str,
    log_bucket_name: str,
    substitutions: Dict[str, str],
    cloud_build_path: str = "cloudbuild.yaml",
    asynchronously: bool = False,
    suppress_logs: bool = False,
    ignore_local_source: bool = False,
) -> str:
    substitutions_string = ",".join(
        [
            substitution_key + "=" + substitution_value
            for substitution_key, substitution_value in substitutions.items()
        ]
    )

    additional_arguments = ""
    if asynchronously:
        additional_arguments += " --async"
    if suppress_logs:
        additional_arguments += " --suppress-logs"
    if ignore_local_source:
        additional_arguments += " --no-source"

    return (
        f"gcloud builds submit "
        f"--region={region} "
        f"--gcs-log-dir=gs://{log_bucket_name} "
        f"--config {cloud_build_path} "
        f"--substitutions "
        f"{substitutions_string}{additional_arguments}"
    )


@task(name="build_cloud_build_training_substitutions")
def build_cloud_build_training_substitutions(
    token_name: str,
    token: str,
    analysis_image_name: ImageNameWithTag,
    model_path: str,
    dvc_remote_name: Optional[str] = None,
    dvc_remote: Optional[str] = None,
    dataset_directory: Optional[str] = None,
) -> dict:
    cloud_build_training_substitutions = {
        "_CI_JOB_TOKEN_NAME": token_name,
        "_CI_JOB_TOKEN": token,
        "_STAGE": STAGE,
        "_ANALYSIS_IMAGE_NAME": analysis_image_name,
        "_TARGET": "training",
    }

    if dvc_remote_name is not None or dvc_remote is not None:
        if dvc_remote_name is None or dvc_remote is None:
            raise ValueError(
                "Both dvc_remote_name and dvc_remote parameters should be specified"
            )

        cloud_build_training_substitutions = {
            **cloud_build_training_substitutions,
            "_DVC_REMOTE_NAME": dvc_remote_name,
            "_DVC_REMOTE": dvc_remote,
        }

    if dataset_directory is not None:
        cloud_build_training_substitutions = {
            **cloud_build_training_substitutions,
            "_DATASET_PATH": os.path.relpath(dataset_directory, model_path),
        }

    return cloud_build_training_substitutions


@task(name="build_cloud_build_serving_substitutions")
def build_cloud_build_serving_substitutions(
    token_name: str, token: str, artifacts_path: GSPath
) -> dict:
    return {
        "_CI_JOB_TOKEN_NAME": token_name,
        "_CI_JOB_TOKEN": token,
        "_STAGE": STAGE,
        "_ARTIFACTS_PATH": artifacts_path,
        "_TARGET": "serving",
    }


@task(name="undeploy_existing_models")
def undeploy_existing_models(name: str):
    vertex_ai_manager = VertexAIManager(
        key_path=GOOGLE_APPLICATION_CREDENTIALS,
        environment=STAGE,
    )

    vertex_ai_manager.undeploy_all_models_by_endpoint_name(name=name)
    vertex_ai_manager.delete_all_models_by_name(name=name)


@task(name="launch_training_job")
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
    storage_client = AccessStorage(GOOGLE_APPLICATION_CREDENTIALS)

    storage_client.create_bucket(models_bucket_name, exist_ok=True)

    job_and_model_name = f"{STAGE}_{model_name}"
    will_produce_model = serving_container_uri is not None

    artifacts_path = None
    if will_produce_model is False:
        timestamp = datetime.now().isoformat(sep="-", timespec="milliseconds")
        artifacts_path = GSPath.from_bucket_and_blob_names(
            models_bucket_name, "-".join([model_name, timestamp])
        )

    job = aiplatform.CustomContainerTrainingJob(
        display_name=job_and_model_name,
        credentials=service_account.Credentials.from_service_account_file(
            GOOGLE_APPLICATION_CREDENTIALS
        ),
        location=location,
        staging_bucket=models_bucket_name,
        container_uri=training_container_uri,
        model_serving_container_image_uri=serving_container_uri,
        command=[
            "python3",
            "-m",
            f"models.{model_name}.train",
        ],
    ).run(
        model_display_name=job_and_model_name if will_produce_model is True else None,
        replica_count=1,  # fixed to 1, we absolutely do not need distributing training
        machine_type=training_machine_type,
        accelerator_type=accelerator_type,
        accelerator_count=accelerator_count,
        base_output_dir=artifacts_path,
    )

    if will_produce_model is True:
        return job.name

    return artifacts_path


@task(name="generate_serving_config")
def generate_serving_config(
    serving_machine_type: str,
    min_replica_count: int,
    max_replica_count: int,
    serving_container_uri: Optional[str] = None,
    serving_predict_route: Optional[str] = None,
    serving_health_route: Optional[str] = None,
    serving_ports: Optional[List[int]] = None,
) -> ServingConfig:
    return ServingConfig(
        machine_type=serving_machine_type,
        min_replica_count=min_replica_count,
        max_replica_count=max_replica_count,
        container_uri=serving_container_uri,
        predict_route=serving_predict_route,
        health_route=serving_health_route,
        ports=serving_ports,
    )


@task(name="build_cloud_build_command")
def build_cloud_build_command(
    region: str, log_bucket_name: str, substitutions: Dict[str, str]
) -> str:
    return generate_cloud_build_command(
        region=region, log_bucket_name=log_bucket_name, substitutions=substitutions
    )


@task(name="overwrite_endpoint_if_existing")
def overwrite_endpoint_if_existing(overwrite_endpoint: str, endpoint_name: str) -> bool:
    overwrite_endpoint = ast.literal_eval(overwrite_endpoint)

    if overwrite_endpoint is True:
        return True

    vertex_ai_manager = VertexAIManager(
        key_path=GOOGLE_APPLICATION_CREDENTIALS,
        environment=STAGE,
    )

    if (
        vertex_ai_manager.get_last_endpoint_by_name(
            name=endpoint_name, allow_higher_environments=False
        )
        is None
    ):
        return True

    return False


@task(name="deploy_model_endpoint")
def deploy_model_endpoint(serving_config: ServingConfig, job_name: str):
    vertex_ai_manager = VertexAIManager(
        key_path=GOOGLE_APPLICATION_CREDENTIALS,
        environment=STAGE,
    )

    vertex_ai_manager.upload_and_deploy_model(job_name, serving_config=serving_config)


def main(
    overwrite_endpoint: bool,
    config: DictConfig,
):
    mode_name = model_config.name
    model_path = f"models/{mode_name}"
    shell_task = ShellTask(
        log_stderr=True,
        stream_output=True,
        helper_script=f"cd {model_path}",
    )

    with Flow(
        name=flow_name,
        result=GCSResult(bucket=config.db.storage.runtime_bucket_name),
    ) as flow:
        token_name = Parameter("token_name", required=True)
        token = Parameter("token", required=True)
        overwrite_endpoint = Parameter("overwrite_endpoint", default="True")

        with case(
            overwrite_endpoint_if_existing(
                overwrite_endpoint, endpoint_name=model_config.name
            ),
            True,
        ):
            cloud_build_training_substitutions = (
                build_cloud_build_training_substitutions(
                    token_name=token_name,
                    token=token,
                    analysis_image_name=ImageNameWithTag(IMAGE_NAME),
                    model_path=model_path,
                    dvc_remote_name=dvc_remote_name,
                    dvc_remote=dvc_remote,
                    dataset_directory=dataset_directory,
                )
            )

            cloud_build_training_task = shell_task(
                command=build_cloud_build_command(
                    region=config.location,
                    log_bucket_name=f"{config.db.storage.runtime_bucket_name}/logs",
                    substitutions=cloud_build_training_substitutions,
                ),
                task_args=dict(name="cloud_build_training_task"),
            )

            artifacts_path = launch_training_job(
                models_bucket_name=config.db.storage.models_bucket_name,
                model_name=model_config.name,
                location=config.location,
                training_container_uri=model_config.training_container_uri,
                training_machine_type=model_config.training_machine_type,
                accelerator_type=model_config.accelerator_type,
                accelerator_count=model_config.accelerator_count,
                upstream_tasks=[cloud_build_training_task],
            )

            cloud_build_serving_substitutions = build_cloud_build_serving_substitutions(
                token_name=token_name, token=token, artifacts_path=artifacts_path
            )

            cloud_build_serving_task = shell_task(
                command=build_cloud_build_command(
                    region=config.location,
                    log_bucket_name=f"{config.db.storage.runtime_bucket_name}/logs",
                    substitutions=cloud_build_serving_substitutions,
                ),
                task_args=dict(name="cloud_build_serving_task"),
            )

            undeploy_existing_models(model_config.name)

            serving_config = generate_serving_config(
                serving_container_uri=model_config.serving_container_uri,
                serving_predict_route=model_config.serving_predict_route,
                serving_health_route=model_config.serving_health_route,
                serving_ports=list(model_config.serving_ports),
                serving_machine_type=model_config.serving_machine_type,
                min_replica_count=model_config.min_replica_count,
                max_replica_count=model_config.max_replica_count,
                upstream_tasks=[cloud_build_serving_task],
            )
            deploy_model_endpoint(
                serving_config=serving_config,
                job_name=model_config.name,
            )

    return flow


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
