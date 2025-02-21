from typing import Optional

import requests

from core.client.api_client import APIClient
from core.routes.model_instantiator import routes
from core.schemas.model_instantiator import (
    CloudSQL,
    InstantiateModelInput,
    UninstantiateModelInput,
)


class ModelInstantiatorClient(APIClient):
    def __init__(self, host: str, key_path: Optional[str] = None):
        super().__init__(host=host, key_path=key_path, root=routes.root)

    def instantiate(
        self, model_name: str, retry_attempts: int = 0
    ) -> requests.Response:
        return self.call(
            resource=f"/{routes.Instantiator.prefix}"
            f"{routes.Instantiator.instantiate}",
            verb="post",
            payload=InstantiateModelInput(model_name=model_name).dict(),
            retry_attempts=retry_attempts,
        )

    def uninstantiate(self, model_name: str) -> requests.Response:
        return self.call(
            resource=f"/{routes.Uninstantiator.prefix}"
            f"{routes.Uninstantiator.uninstantiate}",
            verb="post",
            payload=UninstantiateModelInput(model_name=model_name).dict(),
        )

    def instantiate_cloud_sql(self, cloud_sql_instance_name: str):
        return self.call(
            resource=f"/{routes.Instantiator.prefix}"
            f"{routes.Instantiator.instantiate_cloud_sql}",
            verb="post",
            payload=CloudSQL(instance_name=cloud_sql_instance_name).dict(),
        )

    def uninstantiate_cloud_sql(self, cloud_sql_instance_name: str):
        return self.call(
            resource=f"/{routes.Uninstantiator.prefix}"
            f"{routes.Uninstantiator.cloud_sql_uninstantiate}",
            verb="post",
            payload=CloudSQL(cloud_sql_name=cloud_sql_instance_name).dict(),
        )
