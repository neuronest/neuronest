from abc import ABC
from typing import Optional

from core.client.abstract.mixin import ClientMixin
from core.google.cloud_run_manager import CloudRunManager
from core.schemas.image_name import ImageNameWithTag


class CloudRunBasedClient(ClientMixin, ABC):
    def __init__(self, host: str):
        self.host = host

    def get_underlying_serving_image(
        self, project_id: str, location: str, key_path: Optional[str] = None
    ) -> Optional[ImageNameWithTag]:
        cloud_run_manager = CloudRunManager(
            project_id=project_id,
            location=location,
            key_path=key_path,
        )

        service = cloud_run_manager.get_service_by_host_name(host_name=self.host)

        if service is None:
            return None

        return service.image_name
