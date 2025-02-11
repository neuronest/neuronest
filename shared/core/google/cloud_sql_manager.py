import datetime
import logging
import time
from enum import Enum
from typing import List, Optional

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from core.client.base_client import BaseClient

logger = logging.getLogger(__name__)


class InstanceStatus(str, Enum):
    STARTED = "STARTED"
    STARTING = "STARTING"
    STOPPED = "STOPPED"
    STOPPING = "STOPPING"
    UPDATING = "UPDATING"


class CloudSQLManager(BaseClient):
    def __init__(
        self,
        key_path: Optional[str] = None,
        project_id: Optional[str] = None,
    ):
        super().__init__(key_path=key_path, project_id=project_id)
        self.client = build("sqladmin", "v1", credentials=self.credentials)

    def get_instance_by_name(self, instance_name: str) -> Optional[dict]:
        """
        Get details of a Cloud SQL instance by its name.
        """
        try:
            instance = (
                # pylint: disable=no-member
                self.client.instances()
                .get(
                    project=self.project_id,
                    instance=instance_name,
                )
                .execute()
            )
            return instance
        except HttpError as http_error:
            if http_error.resp.status == 404:
                logger.info(f"Cloud SQL instance '{instance_name}' not found.")
                return None
            logger.error(
                f"Failed to get Cloud SQL instance '{instance_name}': {http_error}"
            )
            raise
        except Exception as error:
            logging.error(f"Unexpected error: {error}")
            raise

    def get_instance_current_activation_policy(self, instance_name: str) -> str:
        """
        Fetch the current activation policy of the Cloud SQL instance.
        """
        instance = self.get_instance_by_name(instance_name)
        return instance["settings"]["activationPolicy"]

    def get_instance_update_operations_history(
        self, instance_name: str
    ) -> Optional[List[dict]]:
        """
        Fetch the status of the most recent 'UPDATE' operation for the specified instance.
        """
        # pylint: disable=no-member
        operations = (
            self.client.operations()
            .list(project=self.project_id, instance=instance_name)
            .execute()
        )

        return [
            operation
            for operation in operations.get("items", [])
            if operation["operationType"] == "UPDATE"
            and instance_name in operation.get("targetLink", "")
        ]

    def get_instance_last_update_operation_status(
        self, instance_name: str
    ) -> Optional[str]:
        """
        Fetch the status of the most recent 'UPDATE' operation for the specified instance.
        """
        # pylint: disable=no-member
        update_operations = self.get_instance_update_operations_history(instance_name)

        if not update_operations:
            return None

        # Return the status of the most recent update operation
        return update_operations[0]["status"]

    def get_instance_last_update_end_time(
        self, instance_name: str
    ) -> Optional[datetime.datetime]:
        """
        Fetch the status of the most recent 'UPDATE' operation for the specified instance.
        """
        # pylint: disable=no-member
        update_operations = self.get_instance_update_operations_history(instance_name)

        if not update_operations:
            return None

        # Return the status of the most recent update operation
        return datetime.datetime.strptime(
            update_operations[0]["endTime"], "%Y-%m-%dT%H:%M:%S.%fZ"
        )

    def get_instance_status(self, instance_name: str) -> InstanceStatus:
        """
        Get the current status of a Cloud SQL instance.

        Args:
            instance_name (str): The name of the Cloud SQL instance.

        Returns:
            InstanceStatus: The current status of the instance.

        Raises:
            ValueError: If the instance status cannot be determined.
        """
        try:
            current_policy = self.get_instance_current_activation_policy(instance_name)

            last_update_status = self.get_instance_last_update_operation_status(
                instance_name
            )

            if current_policy == "ALWAYS" and last_update_status == "RUNNING":
                return InstanceStatus.STARTING
            if current_policy == "ALWAYS" and last_update_status == "DONE":
                return InstanceStatus.STARTED
            if current_policy == "ALWAYS" and last_update_status == "PENDING":
                return InstanceStatus.UPDATING
            if current_policy == "NEVER" and last_update_status == "RUNNING":
                return InstanceStatus.STOPPING
            if current_policy == "NEVER" and last_update_status == "DONE":
                return InstanceStatus.STOPPED

            raise ValueError(
                f"Unhandled case for policy '{current_policy}' "
                f"and last update status '{last_update_status}'."
            )
        except KeyError as key_error:
            raise ValueError(
                f"Error checking instance status: {key_error}"
            ) from key_error
        except Exception as error:
            raise RuntimeError(f"Unexpected error: {error}") from error

    def is_instance_starting(self, instance_name: str) -> bool:
        """
        Check if a Cloud SQL instance is in the process of starting.

        Args:
            instance_name (str): The name of the Cloud SQL instance.

        Returns:
            bool: True if the instance is starting, False otherwise.
        """
        return self.get_instance_status(instance_name) == InstanceStatus.STARTING

    def is_instance_started(self, instance_name: str) -> bool:
        """
        Check if a Cloud SQL instance is fully started.

        Args:
            instance_name (str): The name of the Cloud SQL instance.

        Returns:
            bool: True if the instance is started, False otherwise.
        """
        return self.get_instance_status(instance_name) == InstanceStatus.STARTED

    def is_instance_stopping(self, instance_name: str) -> bool:
        """
        Check if a Cloud SQL instance is in the process of stopping.

        Args:
            instance_name (str): The name of the Cloud SQL instance.

        Returns:
            bool: True if the instance is stopping, False otherwise.
        """
        return self.get_instance_status(instance_name) == InstanceStatus.STOPPING

    def is_instance_stopped(self, instance_name: str) -> bool:
        """
        Check if a Cloud SQL instance is fully stopped.

        Args:
            instance_name (str): The name of the Cloud SQL instance.

        Returns:
            bool: True if the instance is stopped, False otherwise.
        """
        return self.get_instance_status(instance_name) == InstanceStatus.STOPPED

    def _wait_for_operation(self, operation: dict, timeout: int = 600):
        """
        Wait for a Cloud SQL operation to complete.
        """
        operation_name = operation.get("name")
        start_time = time.time()

        while time.time() - start_time < timeout:
            result = (
                # pylint: disable=no-member
                self.client.operations()
                .get(project=self.project_id, operation=operation_name)
                .execute()
            )

            if result.get("status") == "DONE":
                if "error" in result:
                    raise RuntimeError(f"Operation failed: {result['error']}")
                logger.info(f"Operation '{operation_name}' completed successfully.")
                return None

            time.sleep(5)

        raise TimeoutError(
            f"Operation '{operation_name}' timed out after {timeout} seconds."
        )

    def wait_for_instance_update(self, instance_name: str, timeout: int = 600) -> bool:
        """
        Waits for the completion of any ongoing UPDATE operation for the specified
        Cloud SQL instance.

        Args:
            instance_name (str): The name of the Cloud SQL instance.
            timeout (int): The maximum time to wait for operations to complete,
             in seconds.

        Returns:
            bool: True if all operations completed successfully, False if there are
             no ongoing operations.

        Raises:
            RuntimeError: If any operation fails to complete or encounters an error.
        """
        ongoing_operations = [
            operation
            for operation in self.get_instance_update_operations_history(instance_name)
            if operation["status"] != "DONE"
        ]

        if not ongoing_operations:
            logger.info(f"No ongoing update operations for instance '{instance_name}'.")
            return False  # No ongoing operations to wait for

        # Iterate through ongoing operations and wait for their completion
        for operation in ongoing_operations:
            logger.info(
                f"Waiting for operation '{operation['name']}' on "
                f"instance '{instance_name}' to complete. "
                f"Initial status: {operation['status']}."
            )
            try:
                self._wait_for_operation(operation=operation, timeout=timeout)
                logger.info(f"Operation '{operation['name']}' completed successfully.")
            except Exception as error:
                raise RuntimeError(
                    f"Failed to wait for operation '{operation['name']}' "
                    f"on instance '{instance_name}': {error}"
                ) from error

        logger.info(
            f"All ongoing update operations "
            f"for instance '{instance_name}' have completed."
        )
        return True

    def stop_instance(self, instance_name: str, sync: bool = True):
        """
        Stop a Cloud SQL instance.
        """
        instance = self.get_instance_by_name(instance_name)
        if instance is None:
            raise ValueError(f"Instance '{instance_name}' does not exist.")

        if self.is_instance_stopped(instance_name):
            logger.info(f"Instance '{instance_name}' is already stopped.")
            return

        try:
            operation = (
                # pylint: disable=no-member
                self.client.instances()
                .patch(
                    project=self.project_id,
                    instance=instance_name,
                    body={"settings": {"activationPolicy": "NEVER"}},
                )
                .execute()
            )
            if sync:
                self._wait_for_operation(operation)
                logger.info(f"Instance '{instance_name}' has been stopped.")
        except HttpError as http_error:
            logger.error(f"Failed to stop instance '{instance_name}': {http_error}")
            raise

    def start_instance(self, instance_name: str, sync: bool = False):
        """
        Start a Cloud SQL instance with an optional synchronous wait.

        Args:
            instance_name (str): The name of the Cloud SQL instance.
            sync (bool): Whether to wait for the operation to complete (default: True).
        """
        instance = self.get_instance_by_name(instance_name)
        if instance is None:
            raise ValueError(f"Instance '{instance_name}' does not exist.")

        if not self.is_instance_stopped(instance_name):
            logger.info(
                f"Instance '{instance_name}' is already running "
                f"or in the process of starting."
            )
            return

        try:
            # Start the instance by changing the activation policy to "ALWAYS"
            operation = (
                # pylint: disable=no-member
                self.client.instances()
                .patch(
                    project=self.project_id,
                    instance=instance_name,
                    body={"settings": {"activationPolicy": "ALWAYS"}},
                )
                .execute()
            )
            logger.info(f"Start operation initiated for instance '{instance_name}'.")

            if sync:
                self._wait_for_operation(operation)
                logger.info(f"Instance '{instance_name}' has been started.")
        except HttpError as http_error:
            logger.error(f"Failed to start instance '{instance_name}': {http_error}")
            raise
