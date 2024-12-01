import logging
import time
from typing import Optional

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from core.client.base_client import BaseClient

logger = logging.getLogger(__name__)


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
                    instance=instance_name,  # "func-da-neuronest" works
                )  # Use only the instance name
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

    def get_instance_current_activation_policy(self, instance_name: str) -> str:
        """
        Fetch the current activation policy of the Cloud SQL instance.
        """
        instance = self.get_instance_by_name(instance_name)
        return instance["settings"]["activationPolicy"]

    def get_instance_last_update_operation_status(
        self, instance_name: str
    ) -> Optional[str]:
        """
        Fetch the status of the most recent 'UPDATE' operation for the specified instance.
        """
        # pylint: disable=no-member
        operations = self.client.operations().list(project=self.project_id).execute()
        update_operations = [
            operation
            for operation in operations.get("items", [])
            if operation["operationType"] == "UPDATE"
            and instance_name in operation.get("targetLink", "")
        ]

        if not update_operations:
            return None

        # Return the status of the most recent update operation
        return update_operations[0]["status"]

    def is_instance_stopped(self, instance_name: str) -> bool:
        """
        Check if a Cloud SQL instance is stopped.
        """
        try:
            # Get the current activation policy
            current_policy = self.get_instance_current_activation_policy(instance_name)

            # Get the status of the most recent 'UPDATE' operation for this instance
            last_update_status = self.get_instance_last_update_operation_status(
                instance_name
            )

            # Determine if the instance is stopped
            return current_policy == "NEVER" and last_update_status == "DONE"
        except KeyError as key_error:
            raise ValueError(
                f"Error checking instance status: {key_error}"
            ) from key_error
        except Exception as runtime_error:
            raise RuntimeError(f"Unexpected error: {runtime_error}") from runtime_error

    def stop_instance(self, instance_name: str):
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
            self._wait_for_operation(operation)
            logger.info(f"Instance '{instance_name}' has been stopped.")
        except HttpError as http_error:
            logger.error(f"Failed to stop instance '{instance_name}': {http_error}")
            raise

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
                return

            time.sleep(5)

        raise TimeoutError(
            f"Operation '{operation_name}' timed out after {timeout} seconds."
        )


def main():
    # Initialize the CloudSQLManager
    project_id = "database-api-yolo-1"  # Replace with your GCP project ID
    instance_name = "func-da-neuronest"  # Replace with your Cloud SQL instance name

    manager = CloudSQLManager(project_id=project_id)

    try:
        # Check if the instance exists
        instance = manager.get_instance_by_name(instance_name)
        if not instance:
            print(f"Instance '{instance_name}' does not exist.")
            return

        manager.stop_instance(instance_name)

        # Check if the instance is stopped
        if manager.is_instance_stopped(instance_name):
            print(f"Instance '{instance_name}' is currently stopped.")
        else:
            print(f"Instance '{instance_name}' is running.")
    # pylint: disable=broad-exception-caught
    except Exception as exception:
        print(f"An error occurred: {exception}")


if __name__ == "__main__":
    main()
