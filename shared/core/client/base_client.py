from __future__ import annotations

import abc
from typing import Optional

from core.auth import get_credentials


class BaseClient(abc.ABC):
    def __init__(
        self, key_path: Optional[str] = None, project_id: Optional[str] = None
    ):
        self.key_path = key_path
        self.credentials = get_credentials(key_path=self.key_path)
        self._project_id = project_id

    @property
    def project_id(self) -> str:
        # we give priority on the project_id which was passed explicitly to the
        # instantiation rather than to the project id to which the service account
        # of the credentials is attached
        return (
            self._project_id
            if self._project_id is not None
            else self.credentials.project_id
        )
