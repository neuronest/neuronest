import datetime
from enum import Enum
from typing import List, Optional, Tuple

from google.cloud import logging

from core.client.base_client import BaseClient


class LoggerName(str, Enum):
    PREDICTION_CONTAINER = "aiplatform.googleapis.com%2Fprediction_container"


class LoggingClient(BaseClient):
    def __init__(
        self, key_path: Optional[str] = None, project_id: Optional[str] = None
    ):
        super().__init__(key_path=key_path, project_id=project_id)
        self.client = (
            logging.Client(project=self.project_id)
            if key_path is None
            else logging.Client.from_service_account_json(
                json_credentials_path=key_path, project=project_id
            )
        )

    @staticmethod
    def _build_query_elements(
        date: Optional[datetime.datetime] = None,
        messages: Tuple[str, ...] = (),
    ) -> List[str]:
        query_elements = []

        if date is not None:
            query_elements.append(
                f"timestamp>=\"{date.strftime('%Y-%m-%dT%H:%M:%SZ')}\""
            )

        for message in messages:
            query_elements.append(f"jsonPayload.message:{message}")

        return query_elements

    @classmethod
    def _build_query(
        cls,
        date: Optional[datetime.datetime] = None,
        messages: Tuple[str, ...] = (),
    ) -> Optional[str]:
        if date is None and len(messages) == 0:
            return None

        return " AND ".join(cls._build_query_elements(date=date, messages=messages))

    def get_filtered_logs(
        self,
        logger_name: str,
        date: Optional[datetime.datetime] = None,
        messages: Tuple[str, ...] = (),
    ):
        logger = self.client.logger(logger_name)

        date_utc = date.astimezone(datetime.timezone.utc)

        return list(
            logger.list_entries(
                filter_=self._build_query(date=date_utc, messages=messages)
            )
        )
