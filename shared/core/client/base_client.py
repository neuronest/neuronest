from __future__ import annotations

import abc
from typing import Optional

from core.auth import get_credentials
from core.google.utils import get_service_account_name_project_id_from_email


class BaseClient(abc.ABC):
    def __init__(
        self, key_path: Optional[str] = None, project_id: Optional[str] = None
    ):
        self.key_path = key_path
        self.credentials = get_credentials(key_path=self.key_path)
        self._project_id = project_id

    @property
    def project_id(self) -> str:
        """
        Retrieve the project ID associated with this instance.

        Priority is given to the explicitly passed `_project_id` during instantiation.
        If `_project_id` is not set, the function attempts to retrieve the project ID
        from the `credentials`.

        Note:
        - For impersonated credentials, the `project_id` attribute is not present.
          In such cases, the function derives the project ID from the
          `service_account_email`.

        Returns:
            str: The project ID associated with the credentials or the explicitly
             set value.
        """
        if self._project_id is not None:
            return self._project_id
        if hasattr(self.credentials, "project_id"):
            return self.credentials.project_id

        # Derive project ID from the service account email in impersonated credentials
        _, project_id = get_service_account_name_project_id_from_email(
            service_account_email=self.credentials.service_account_email
        )

        return project_id
