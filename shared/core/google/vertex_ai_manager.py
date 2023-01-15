import logging
from typing import List, Optional

from google.cloud import aiplatform, aiplatform_v1
from google.cloud.aiplatform_v1.types import training_pipeline
from google.oauth2 import service_account

from core.exceptions import AlreadyExistingError
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

    def get_all_models_by_name(self, name: str) -> List[aiplatform.Model]:
        return aiplatform.models.Model.list(
            location=self.location,
            credentials=self.credentials,
            project=self.project_id,
            filter=f"display_name={name}",
            order_by="create_time desc",
        )

    def get_all_endpoints_by_name(self, name: str) -> List[aiplatform.Endpoint]:
        return aiplatform.Endpoint.list(
            location=self.location,
            credentials=self.credentials,
            project=self.project_id,
            filter=f"display_name={self._model_to_endpoint_name(name)}",
            order_by="create_time desc",
        )

    def get_last_model_by_name(
        self,
        name: str,
    ) -> Optional[aiplatform.Model]:
        models = self.get_all_models_by_name(name)

        if len(models) == 0:
            return None

        return models[0]

    def get_last_endpoint_by_name(
        self,
        name: str,
    ) -> Optional[aiplatform.Endpoint]:
        endpoints = self.get_all_endpoints_by_name(name)

        if len(endpoints) == 0:
            return None

        return endpoints[0]

    def get_model_by_id(self, model_id: str) -> Optional[aiplatform.Model]:
        return aiplatform.models.Model(
            location=self.location, credentials=self.credentials, model_name=model_id
        )

    def undeploy_all_models_by_endpoint_name(self, name: str):
        endpoint = self.get_last_endpoint_by_name(name)

        if endpoint is None:
            logger.warning(f"No endpoint named '{name}' has been found")

        if endpoint is not None:
            endpoint.undeploy_all()

    def delete_all_models_by_name(self, name: str):
        models = self.get_all_models_by_name(name)

        for model in models:
            model.delete()

    def delete_endpoint(self, name: str, remove_models: bool = False):
        endpoint = self.get_last_endpoint_by_name(name)

        if endpoint is None:
            logger.warning(f"No endpoint named '{name}' has been found")

        endpoint.delete(force=remove_models)

    def upload_model(
        self,
        name: str,
        serving_model_upload_config: ServingModelUploadConfig,
    ) -> aiplatform.Model:
        existing_model = self.get_last_model_by_name(name=name)

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
        )

    def deploy_model(
        self,
        name: str,
        model: aiplatform.Model,
        serving_deployment_config: ServingDeploymentConfig,
        sync: bool = True,
        timeout: float = 1800,
    ) -> aiplatform.Endpoint:
        endpoint = self.get_last_endpoint_by_name(name)

        if endpoint is not None:
            raise AlreadyExistingError(
                f"The model '{name}' is already deployed on endpoint "
                f"{endpoint.resource_name}"
            )

        return model.deploy(
            endpoint=endpoint,
            deployed_model_display_name=name,
            traffic_split={"0": 100},  # the new deployment receives 100% of the traffic
            machine_type=serving_deployment_config.machine_type,
            min_replica_count=serving_deployment_config.min_replica_count,
            max_replica_count=serving_deployment_config.max_replica_count,
            accelerator_type=serving_deployment_config.accelerator_type,
            accelerator_count=serving_deployment_config.accelerator_count,
            sync=sync,
            deploy_request_timeout=timeout,
        )
