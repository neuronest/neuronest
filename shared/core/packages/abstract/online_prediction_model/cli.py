from __future__ import annotations

import abc
import argparse
import inspect
import logging
import sys
from enum import Enum
from typing import Dict, Optional, Tuple, Type

from google.cloud import aiplatform

from core.client.model_instantiator import ModelInstantiatorClient
from core.google.storage_client import StorageClient
from core.google.vertex_ai_manager import VertexAIManager
from core.packages.abstract.online_prediction_model.config import Config
from core.packages.abstract.online_prediction_model.environment_variables import (
    GOOGLE_APPLICATION_CREDENTIALS,
    MODEL_INSTANTIATOR_HOST,
    PROJECT_ID,
    TRAINING_IMAGE_NAME,
    VERTEX_LOCATION,
)
from core.path import GSPath
from core.schemas.vertex_ai import (
    ServingDeploymentConfig,
    ServingModelUploadConfig,
    TrainingConfig,
)

logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)


class Action(str, Enum):
    TRAIN = "train"
    MODEL_UPLOAD = "model_upload"


class RunnableAction(abc.ABC):
    action: Optional[Action] = None
    kwargs: Tuple[str, ...] = tuple()

    @staticmethod
    def build_training_config(config: Config) -> TrainingConfig:
        return TrainingConfig(**config.training.model_dump())

    @staticmethod
    def build_serving_model_upload_config(
        config: Config,
    ) -> ServingModelUploadConfig:
        return ServingModelUploadConfig(**config.serving_model_upload.model_dump())

    @staticmethod
    def build_serving_deployment_config(config: Config) -> ServingDeploymentConfig:
        return ServingDeploymentConfig(**config.serving_deployment.model_dump())

    @classmethod
    @abc.abstractmethod
    def run(
        cls,
        **kwargs,
    ) -> str:
        raise NotImplementedError()


class LaunchTrainingJobAction(RunnableAction):
    action = Action.TRAIN
    kwargs = (
        "config",
        "vertex_ai_manager",
        "model_name",
        "model_gspath",
    )

    @classmethod
    # pylint: disable=arguments-differ
    def run(
        cls,
        config: Config,
        vertex_ai_manager: VertexAIManager,
        model_name: str,
        model_gspath: GSPath,
        **kwargs,
    ):
        training_config: TrainingConfig = cls.build_training_config(config)

        if model_gspath is None:
            raise ValueError(
                "model_gspath parameter should be specified in training action"
            )

        models_bucket_name, _ = model_gspath.to_bucket_and_blob_names()
        if (
            StorageClient(project_id=PROJECT_ID).bucket_exists(
                bucket_name=models_bucket_name,
            )
            is False
        ):
            raise ValueError(f"The bucket '{models_bucket_name}' does not exist")

        # unspecified: it won't produce a Vertex Model because no
        # model_serving_container_image_uri is specified (a custom one will be created)
        model_display_name = None

        training_job = aiplatform.CustomContainerTrainingJob(
            display_name=model_name,
            location=vertex_ai_manager.location,
            staging_bucket=models_bucket_name,
            container_uri=training_config.container_uri,
            command=["python3", "-m", f"{config.package_name}.train"],
        )

        # will raise a RuntimeError if the job itself crashed
        training_job.run(
            service_account=config.service_account,
            model_display_name=model_display_name,
            replica_count=training_config.replica_count,
            machine_type=training_config.machine_type,
            accelerator_type=training_config.accelerator_type,
            accelerator_count=training_config.accelerator_count,
            base_output_dir=model_gspath,
            environment_variables={
                "IMAGE_NAME": TRAINING_IMAGE_NAME,
                "PROJECT_ID": vertex_ai_manager.project_id,
                "REGION": vertex_ai_manager.location,
            },
        )


class UploadModelAction(RunnableAction):
    action = Action.MODEL_UPLOAD
    kwargs = (
        "config",
        "vertex_ai_manager",
        "model_name",
    )

    @classmethod
    # pylint: disable=arguments-differ
    def run(
        cls,
        config: Config,
        vertex_ai_manager: VertexAIManager,
        model_name: str,
        **kwargs,
    ) -> aiplatform.Model:
        serving_model_upload_config: ServingModelUploadConfig = (
            cls.build_serving_model_upload_config(config)
        )
        serving_deployment_config: ServingDeploymentConfig = (
            cls.build_serving_deployment_config(config)
        )

        return vertex_ai_manager.upload_model(
            name=model_name,
            serving_model_upload_config=serving_model_upload_config,
            serving_deployment_config=serving_deployment_config,
        )


class ActionFactory:
    _actions: Dict[Action, Type[RunnableAction]] = {}

    for _, cls in inspect.getmembers(sys.modules[__name__], inspect.isclass):
        if not issubclass(cls, RunnableAction):
            continue

        if cls.action is None:
            continue

        _actions[cls.action] = cls

    @classmethod
    def new(cls, action: Action) -> Type[RunnableAction]:
        return cls._actions[action]


def main(config: Config):
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-gspath", dest="model_gspath")
    parser.add_argument(
        "--actions",
        dest="actions",
        choices=list(Action),
        nargs="+",
    )
    parsed_args = parser.parse_args()

    if len(parsed_args.actions) == 0:
        raise ValueError("No action received")

    model_gspath = (
        None if parsed_args.model_gspath is None else GSPath(parsed_args.model_gspath)
    )
    actions = [Action(action) for action in parsed_args.actions]

    vertex_ai_manager = VertexAIManager(
        key_path=GOOGLE_APPLICATION_CREDENTIALS,
        location=VERTEX_LOCATION,
        project_id=PROJECT_ID,
    )
    if MODEL_INSTANTIATOR_HOST is not None:
        model_instantiator_client = ModelInstantiatorClient(
            key_path=GOOGLE_APPLICATION_CREDENTIALS, host=MODEL_INSTANTIATOR_HOST
        )
    else:
        model_instantiator_client = None
    model_name = config.model.name

    parameters = {
        "config": config,
        "vertex_ai_manager": vertex_ai_manager,
        "model_instantiator_client": model_instantiator_client,
        "model_name": model_name,
        "model_gspath": model_gspath,
    }

    for action in actions:
        ActionFactory.new(action).run(**parameters)


if __name__ == "__main__":
    cfg = None  # pylint: disable=invalid-name
    # we encapsulate 100 % of the logic in a single function to be imported and reused
    # in specialized repositories and we delegate to those repositories the only things
    # that are not known in advance: the config
    main(config=cfg)
