import logging
import time
from typing import List, Optional, Tuple

from google.cloud import aiplatform, aiplatform_v1
from google.cloud.aiplatform_v1.types import training_pipeline
from google.oauth2 import service_account

from core.schemas.vertex_ai import ServingDeploymentConfig, ServingModelUploadConfig

logger = logging.getLogger(__name__)


class VertexAIManager:
    def __init__(
        self,
        location: str,
        key_path: Optional[str] = None,
        project_id: Optional[str] = None,
    ):
        self.location = location

        if key_path is None and project_id is None:
            raise ValueError("Either key_path or project_id should be specified")

        self.credentials = (
            service_account.Credentials.from_service_account_file(key_path)
            if key_path is not None
            else None
        )
        self._project_id = project_id

        client_options = {"api_endpoint": f"{self.location}-aiplatform.googleapis.com"}
        # noinspection PyTypeChecker
        self.pipeline_service_client = aiplatform.gapic.PipelineServiceClient(
            credentials=self.credentials, client_options=client_options
        )

    @property
    def project_id(self) -> str:
        return (
            self.credentials.project_id
            if self.credentials is not None
            else self._project_id
        )

    @staticmethod
    def _model_to_endpoint_name(model_name: str) -> str:
        if model_name == "":
            raise ValueError("Incorrect model_name")

        return f"{model_name}_endpoint"

    def _get_all_models_by_name(self, name: str) -> List[aiplatform.Model]:
        return aiplatform.models.Model.list(
            location=self.location,
            credentials=self.credentials,
            project=self.project_id,
            filter=f"display_name={name}",
            order_by="create_time desc",
        )

    def _get_all_endpoints_by_name(self, name: str) -> List[aiplatform.Endpoint]:
        return aiplatform.Endpoint.list(
            location=self.location,
            credentials=self.credentials,
            project=self.project_id,
            filter=f"display_name={self._model_to_endpoint_name(name)}",
            order_by="create_time desc",
        )

    def list_training_pipelines(self) -> List[training_pipeline.TrainingPipeline]:
        parent = f"projects/{self.project_id}/locations/{self.location}"
        request = aiplatform_v1.ListTrainingPipelinesRequest({"parent": parent})

        return list(
            self.pipeline_service_client.list_training_pipelines(request=request)
        )

    def get_training_pipeline_by_id(
        self,
        training_pipeline_id: str,
    ) -> training_pipeline.TrainingPipeline:
        name = self.pipeline_service_client.training_pipeline_path(
            project=self.project_id,
            location=self.location,
            training_pipeline=training_pipeline_id,
        )

        return self.pipeline_service_client.get_training_pipeline(name=name)

    def get_model_by_id(self, model_id: str) -> Optional[aiplatform.Model]:
        return aiplatform.models.Model(
            location=self.location, credentials=self.credentials, model_name=model_id
        )

    def get_model_by_name(
        self, name: str, version_aliases: Tuple[str, ...] = ("default",)
    ) -> Optional[aiplatform.Model]:
        models = [
            model
            for model in self._get_all_models_by_name(name)
            if tuple(model.version_aliases) == version_aliases
        ]

        if len(models) == 0:
            return None

        if len(models) == 1:
            return models[0]

        raise ValueError(f"Multiple models found with the same name: {name}")

    def get_endpoint_by_name(
        self,
        name: str,
    ) -> Optional[aiplatform.Endpoint]:
        endpoints = self._get_all_endpoints_by_name(name)

        if len(endpoints) == 0:
            return None

        if len(endpoints) == 1:
            return endpoints[0]

        raise ValueError(f"Multiple endpoints found with the same name: {name}")

    def undeploy_models_without_traffic_by_endpoint_name(self, name: str):
        endpoint = self.get_endpoint_by_name(name)

        if endpoint is None:
            logger.warning(f"No endpoint named '{name}' has been found")
            return

        for deployed_model in endpoint.gca_resource.deployed_models:
            if endpoint.traffic_split.get(deployed_model.id, 0) == 0:
                endpoint.undeploy(deployed_model_id=deployed_model.id)

    def undeploy_all_models_by_endpoint_name(self, name: str):
        endpoint = self.get_endpoint_by_name(name)

        if endpoint is None:
            logger.warning(f"No endpoint named '{name}' has been found")

        if endpoint is not None:
            endpoint.undeploy_all()

    def delete_model_by_name(self, name: str):
        model = self.get_model_by_name(name)

        if model is None:
            logger.warning(f"No model named '{name}' has been found")

        model.delete()

    def delete_endpoint(self, name: str, undeploy_models: bool = False):
        endpoint = self.get_endpoint_by_name(name)

        if endpoint is None:
            logger.warning(f"No endpoint named '{name}' has been found")

        endpoint.delete(force=undeploy_models)

    def upload_model(
        self,
        name: str,
        serving_model_upload_config: ServingModelUploadConfig,
        serving_deployment_config: ServingDeploymentConfig,
    ) -> aiplatform.Model:
        existing_model = self.get_model_by_name(name=name)

        if existing_model is None:
            parent_model = None
        else:
            parent_model = existing_model.resource_name

        return aiplatform.Model.upload(
            project=self.project_id,
            parent_model=parent_model,
            display_name=name,
            location=self.location,
            serving_container_image_uri=serving_model_upload_config.container_uri,
            serving_container_predict_route=serving_model_upload_config.predict_route,
            serving_container_health_route=serving_model_upload_config.health_route,
            serving_container_ports=serving_model_upload_config.ports,
            labels=serving_deployment_config.as_labels(),
        )

    def is_model_deployed(self, name: str, model: aiplatform.Model) -> bool:
        endpoint = self.get_endpoint_by_name(name)

        for deployed_model in endpoint.gca_resource.deployed_models:
            if (
                endpoint.traffic_split.get(deployed_model.id) == 100
                and deployed_model.model_version_id == model.version_id
            ):
                return True

        return False

    def wait_for_model_deployed(
        self,
        name: str,
        model: aiplatform.Model,
        timeout: float = 1800,
        check_frequency: float = 30,
        current_time: float = 0,
    ):
        if current_time >= timeout:
            return False

        if self.is_model_deployed(name=name, model=model):
            return True

        time.sleep(check_frequency)

        return self.wait_for_model_deployed(
            name=name,
            model=model,
            timeout=timeout,
            current_time=current_time + check_frequency,
        )

    def deploy_model(
        self,
        name: str,
        model: aiplatform.Model,
        serving_deployment_config: ServingDeploymentConfig,
        undeploy_previous_model: bool = True,
        timeout: float = 1800,
    ) -> aiplatform.Endpoint:
        endpoint = self.get_endpoint_by_name(name)

        for deployed_model in endpoint.gca_resource.deployed_models:
            if (
                endpoint.traffic_split.get(deployed_model.id) == 100
                and deployed_model.model_version_id == model.version_id
            ):
                # for a given model version,
                # there should be only one deployed model with 100% traffic
                return endpoint

        endpoint = model.deploy(
            endpoint=endpoint,
            deployed_model_display_name=name,
            traffic_split={"0": 100},  # the new deployment receives 100% of the traffic
            machine_type=serving_deployment_config.machine_type,
            min_replica_count=serving_deployment_config.min_replica_count,
            max_replica_count=serving_deployment_config.max_replica_count,
            accelerator_type=serving_deployment_config.accelerator_type,
            accelerator_count=serving_deployment_config.accelerator_count,
            # sync=True doesn't seem to be trusted as it can timeout without being able
            # to do anything about it
            # (deploy_request_timeout parameter seems to be ineffective)
            sync=False,
        )

        if not self.wait_for_model_deployed(name=name, model=model, timeout=timeout):
            raise TimeoutError(
                f"Model '{name}' could not been deployed after {timeout} seconds"
            )

        if undeploy_previous_model:
            self.undeploy_models_without_traffic_by_endpoint_name(name)

        return endpoint
