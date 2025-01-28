from typing import Optional

import requests

from core.client.api_client import APIClient
from core.routes.model_instantiator import routes
from core.schemas.model_instantiator import (
    InstantiateCloudSQLInput,
    UninstantiateCloudSqlInput,
    UninstantiateModelInput,
)


class ModelInstantiatorClient(APIClient):
    def __init__(self, host: str, key_path: Optional[str] = None):
        super().__init__(host=host, key_path=key_path, root=routes.root)

    def instantiate(self, model_name: str) -> requests.Response:
        return self.call(
            resource=f"/{routes.Instantiator.prefix}"
            f"{routes.Instantiator.instantiate}",
            verb="post",
            payload=InstantiateCloudSQLInput(model_name=model_name).dict(),
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
            payload=InstantiateCloudSQLInput(
                instance_name=cloud_sql_instance_name
            ).dict(),
        )

    def uninstantiate_cloud_sql(self, cloud_sql_instance_name: str):
        return self.call(
            resource=f"/{routes.Uninstantiator.prefix}"
            f"{routes.Uninstantiator.cloud_sql_uninstantiate}",
            verb="post",
            payload=UninstantiateCloudSqlInput(
                cloud_sql_name=cloud_sql_instance_name
            ).dict(),
        )
