from typing import List, Optional

from google.cloud.exceptions import NotFound
from google.cloud.run_v2 import GetServiceRequest, ListServicesRequest, ServicesClient

from core.auth import get_credentials
from core.schemas.google.cloud_run import ServiceSchema
from core.serialization.protobuf import protobuf_to_dict


class CloudRunManager:
    def __init__(self, project_id: str, location: str, key_path: Optional[str] = None):
        self._credentials = (
            get_credentials(key_path=key_path) if key_path is not None else None
        )
        self._parent = f"projects/{project_id}/locations/{location}"
        self.services_client = ServicesClient(credentials=self._credentials)
        self.project_id = project_id
        self.location = location

    def get_service_by_name(self, service_name: str) -> Optional[ServiceSchema]:
        # noinspection PyTypeChecker
        request = GetServiceRequest(name=f"{self._parent}/services/{service_name}")

        try:
            response = self.services_client.get_service(request=request)
        except NotFound:
            return None

        return ServiceSchema.parse_obj(protobuf_to_dict(response))

    def get_service_by_host_name(self, host_name: str) -> Optional[ServiceSchema]:
        services = self.list_services()

        matching_services = [
            service for service in services if service.short_name in host_name
        ]

        if len(matching_services) == 0:
            return None

        if len(matching_services) > 1:
            raise ValueError(f"Multiple services found having host_name={host_name}")

        matching_service = matching_services[0]

        return self.get_service_by_name(service_name=matching_service.short_name)

    def list_services(self) -> List[ServiceSchema]:
        # noinspection PyTypeChecker
        request = ListServicesRequest(parent=self._parent)

        responses = self.services_client.list_services(request=request)

        return [
            ServiceSchema.parse_obj(protobuf_to_dict(response))
            for response in list(responses)
        ]
