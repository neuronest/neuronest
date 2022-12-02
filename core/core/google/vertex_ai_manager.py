import logging
from dataclasses import dataclass
from typing import List, Optional

from google.cloud import aiplatform
from google.oauth2 import service_account

from neuronest.core.schemas.environment import Environment

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
    def __init__(self, key_path: str, environment: Environment, location: str):
        self.credentials = service_account.Credentials.from_service_account_file(
            key_path
        )
        self.environment = Environment(environment)
        self.location = location

    def get_display_name(self, name: str, environment: Optional[Environment] = None):
        environment = environment or self.environment
        return f"{environment}_{name}"

    def get_all_models_by_name(
        self, name: str, environment: Optional[Environment] = None
    ) -> List[aiplatform.Model]:
        return aiplatform.models.Model.list(
            location=self.location,
            credentials=self.credentials,
            filter=f"display_name={self.get_display_name(name, environment)}",
            order_by="create_time desc",
        )

    def get_all_endpoints_by_name(
        self, name: str, environment: Optional[Environment] = None
    ) -> List[aiplatform.Endpoint]:
        return aiplatform.Endpoint.list(
            location=self.location,
            credentials=self.credentials,
            filter=f"display_name={self.get_display_name(name, environment)}_endpoint",
            order_by="create_time desc",
        )

    def get_last_model_by_name(
        self,
        name: str,
    ) -> Optional[aiplatform.Model]:
        models = self.get_all_models_by_name(name, self.environment)

        if len(models) == 0:
            return None

        return models[0]

    def get_last_endpoint_by_name(
        self,
        name: str,
        allow_higher_environments: bool = True,
        environment: Optional[Environment] = None,
    ) -> Optional[aiplatform.Endpoint]:
        environment = environment or self.environment

        endpoints = self.get_all_endpoints_by_name(name, environment)

        if len(endpoints) == 0:
            higher_environment = environment.get_higher_environment()
            if allow_higher_environments and higher_environment is not None:
                logger.warning(
                    f"No endpoint named '{name}' has been found, "
                    f"retrying with a higher environment: {higher_environment}"
                )
                return self.get_last_endpoint_by_name(
                    name=name,
                    allow_higher_environments=allow_higher_environments,
                    environment=higher_environment,
                )

            logger.warning(f"No endpoint named '{name}' has been found")
            return None

        return endpoints[0]

    def get_model_by_id(self, model_id: str) -> Optional[aiplatform.Model]:
        return aiplatform.models.Model(
            location=self.location, credentials=self.credentials, model_name=model_id
        )

    def undeploy_all_models_by_endpoint_name(self, name: str):
        endpoint = self.get_last_endpoint_by_name(name, allow_higher_environments=False)

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
        endpoint = self.get_last_endpoint_by_name(name, allow_higher_environments=False)

        model.deploy(
            endpoint=endpoint,
            deployed_model_display_name=self.get_display_name(name),
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
            display_name=self.get_display_name(name),
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
