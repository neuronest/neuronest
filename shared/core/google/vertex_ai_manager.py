import logging
from dataclasses import dataclass
from typing import List, Optional

from google.cloud import aiplatform, aiplatform_v1
from google.cloud.aiplatform_v1.types import training_pipeline
from google.oauth2 import service_account

logger = logging.getLogger(__name__)


@dataclass
class ServingConfig:
    machine_type: str
    min_replica_count: int
    max_replica_count: int
    # the following fields are used for custom containers
    container_uri: Optional[str] = None
    predict_route: Optional[str] = None
    health_route: Optional[str] = None
    ports: Optional[List[int]] = None


class VertexAIManager:
    def __init__(self, key_path: str, location: str):
        self.credentials = service_account.Credentials.from_service_account_file(
            key_path
        )
        self.location = location

        client_options = {"api_endpoint": f"{self.location}-aiplatform.googleapis.com"}
        # noinspection PyTypeChecker
        self.pipeline_service_client = aiplatform.gapic.PipelineServiceClient(
            credentials=self.credentials, client_options=client_options
        )

    def list_training_pipelines(self) -> List[training_pipeline.TrainingPipeline]:
        parent = f"projects/{self.credentials.project_id}/locations/{self.location}"
        request = aiplatform_v1.ListTrainingPipelinesRequest({"parent": parent})

        return list(
            self.pipeline_service_client.list_training_pipelines(request=request)
        )

    def get_training_pipeline_by_id(
        self,
        training_pipeline_id: str,
    ) -> training_pipeline.TrainingPipeline:
        name = self.pipeline_service_client.training_pipeline_path(
            project=self.credentials.project_id,
            location=self.location,
            training_pipeline=training_pipeline_id,
        )

        return self.pipeline_service_client.get_training_pipeline(name=name)

    def get_all_models_by_name(self, name: str) -> List[aiplatform.Model]:
        return aiplatform.models.Model.list(
            location=self.location,
            credentials=self.credentials,
            filter=f"display_name={name}",
            order_by="create_time desc",
        )

    def get_all_endpoints_by_name(self, name: str) -> List[aiplatform.Endpoint]:
        return aiplatform.Endpoint.list(
            location=self.location,
            credentials=self.credentials,
            filter=f"display_name={name}_endpoint",
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
            logger.warning(f"No endpoint named '{name}' has been found")
            return None

        return endpoints[0]

    def get_model_by_id(self, model_id: str) -> Optional[aiplatform.Model]:
        return aiplatform.models.Model(
            location=self.location, credentials=self.credentials, model_name=model_id
        )

    def undeploy_all_models_by_endpoint_name(self, name: str):
        endpoint = self.get_last_endpoint_by_name(name)

        if endpoint is not None:
            endpoint.undeploy_all()

    def delete_all_models_by_name(self, name: str):
        models = self.get_all_models_by_name(name)

        for model in models:
            model.delete()

    def deploy_model(
        self,
        name: str,
        model: aiplatform.Model,
        serving_config: ServingConfig,
    ):
        endpoint = self.get_last_endpoint_by_name(name)

        model.deploy(
            endpoint=endpoint,
            deployed_model_display_name=name,
            traffic_split={"0": 100},  # the new deployment receives 100% of the traffic
            machine_type=serving_config.machine_type,
            min_replica_count=serving_config.min_replica_count,
            max_replica_count=serving_config.max_replica_count,
        )

    def upload_and_deploy_model(
        self,
        name: str,
        serving_config: ServingConfig,
    ):
        model = aiplatform.Model.upload(
            display_name=name,
            location=self.location,
            credentials=self.credentials,
            serving_container_image_uri=serving_config.container_uri,
            serving_container_predict_route=serving_config.predict_route,
            serving_container_health_route=serving_config.health_route,
            serving_container_ports=serving_config.ports,
        )

        self.deploy_model(
            name=name,
            model=model,
            serving_config=serving_config,
        )
