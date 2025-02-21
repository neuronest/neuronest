import datetime
import logging
import time
from enum import Enum
from typing import Dict, List, Optional

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pydantic import BaseModel, validator

from core.client.base_client import BaseClient

logger = logging.getLogger(__name__)


class ActivationPolicy(str, Enum):
    ALWAYS = "ALWAYS"
    NEVER = "NEVER"


class Settings(BaseModel):
    activationPolicy: ActivationPolicy


class InstancePatchBody(BaseModel):
    settings: Settings


class Instance(BaseModel):
    settings: Settings


class InstanceStatus(str, Enum):
    STARTED = "STARTED"
    STARTING = "STARTING"
    STOPPED = "STOPPED"
    STOPPING = "STOPPING"
    UPDATING = "UPDATING"


class OperationStatus(str, Enum):
    DONE = "DONE"
    RUNNING = "RUNNING"
    PENDING = "PENDING"


class OperationType(str, Enum):
    UPDATE = "UPDATE"
    # Add other operation types as needed


DATETIME_FORMAT_WITH_MICROSECONDS = "%Y-%m-%dT%H:%M:%S.%fZ"
DATETIME_FORMAT_WITHOUT_MICROSECONDS = "%Y-%m-%dT%H:%M:%SZ"


class Operation(BaseModel):
    name: str
    status: Optional[str]  # Now optional, accepts None or any string
    operationType: Optional[str]
    targetLink: Optional[str]
    endTime: Optional[str]
    error: Optional[Dict] = None  # Now accepts None or str, and handles missing field

    @validator("status", pre=True, always=True)
    # pylint: disable=no-self-argument
    def validate_status(cls, status):
        if status == OperationStatus.DONE.value:
            return status
        return status  # Accept unknown statuses

    @validator("operationType", pre=True, always=True)
    # pylint: disable=no-self-argument
    def validate_operation_type(cls, operation_type):
        if operation_type not in OperationType.__members__.values():
            return operation_type  # Accept unknown operation types
        return operation_type

    @validator("endTime", pre=True, always=True)
    # pylint: disable=no-self-argument
    def validate_end_time_format(cls, end_time):
        if end_time is not None:
            for date_format in [
                DATETIME_FORMAT_WITH_MICROSECONDS,
                DATETIME_FORMAT_WITHOUT_MICROSECONDS,
            ]:
                try:
                    datetime.datetime.strptime(end_time, date_format)
                    return end_time
                except ValueError:
                    continue
            raise ValueError(
                f"endTime must follow the format '{DATETIME_FORMAT_WITH_MICROSECONDS}' "
                f"or '{DATETIME_FORMAT_WITHOUT_MICROSECONDS}'"
            )
        return end_time

    @property
    def end_time_datetime(self) -> Optional[datetime]:
        if self.endTime:
            for fmt in [
                DATETIME_FORMAT_WITH_MICROSECONDS,
                DATETIME_FORMAT_WITHOUT_MICROSECONDS,
            ]:
                try:
                    return datetime.datetime.strptime(self.endTime, fmt)
                except ValueError:
                    continue
        return None


class InstanceOperations(BaseModel):
    items: Optional[List[Operation]] = None

    def get_update_operations(self, instance_name: str) -> List[Operation]:
        if not self.items:
            return []

        return [
            operation
            for operation in self.items  # pylint: disable=not-an-iterable
            if operation.operationType == OperationType.UPDATE
            and operation.targetLink
            and instance_name in operation.targetLink
        ]


class CloudSQLManager(BaseClient):
    def __init__(
        self,
        key_path: Optional[str] = None,
        project_id: Optional[str] = None,
    ):
        super().__init__(key_path=key_path, project_id=project_id)
        self.client = build("sqladmin", "v1", credentials=self.credentials)

    def get_instance_by_name(self, instance_name: str) -> Optional[Instance]:
        """
        Get details of a Cloud SQL instance by its name.
        """
        try:
            instance = Instance(
                **(
                    # pylint: disable=no-member
                    self.client.instances()
                    .get(
                        project=self.project_id,
                        instance=instance_name,
                    )
                    .execute()
                )
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
        return instance.settings.activationPolicy

    def get_instance_update_operations_history(
        self, instance_name: str
    ) -> List[Operation]:
        """
        Fetch the status of the most recent 'UPDATE' operation for the specified instance.
        """
        # pylint: disable=no-member
        operations = InstanceOperations(
            **(
                self.client.operations()
                .list(project=self.project_id, instance=instance_name)
                .execute()
            )
        )

        return operations.get_update_operations(instance_name)

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
        return update_operations[0].status

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
        return datetime.datetime.strptime(update_operations[0].end_time_datetime)

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

            if (
                current_policy == ActivationPolicy.ALWAYS
                and last_update_status == OperationStatus.RUNNING
            ):
                return InstanceStatus.STARTING
            if (
                current_policy == ActivationPolicy.ALWAYS
                and last_update_status == OperationStatus.DONE
            ):
                return InstanceStatus.STARTED
            if (
                current_policy == ActivationPolicy.ALWAYS
                and last_update_status == OperationStatus.PENDING
            ):
                return InstanceStatus.UPDATING
            if (
                current_policy == ActivationPolicy.NEVER
                and last_update_status == OperationStatus.RUNNING
            ):
                return InstanceStatus.STOPPING
            if (
                current_policy == ActivationPolicy.NEVER
                and last_update_status == OperationStatus.DONE
            ):
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

    def _wait_for_operation(self, operation: Operation, timeout: int = 600):
        """
        Wait for a Cloud SQL operation to complete.
        """
        operation_name = operation.name
        start_time = time.time()

        while time.time() - start_time < timeout:
            operation = Operation(
                **(
                    # pylint: disable=no-member
                    self.client.operations()
                    .get(project=self.project_id, operation=operation_name)
                    .execute()
                )
            )

            if operation.status == OperationStatus.DONE:
                if operation.error:
                    raise RuntimeError(f"Operation failed: {operation.error}")
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
            if operation.status != OperationStatus.DONE
        ]

        if not ongoing_operations:
            logger.info(f"No ongoing update operations for instance '{instance_name}'.")
            return False  # No ongoing operations to wait for

        # Iterate through ongoing operations and wait for their completion
        for operation in ongoing_operations:
            logger.info(
                f"Waiting for operation '{operation.name}' on "
                f"instance '{instance_name}' to complete. "
                f"Initial status: {operation.status}."
            )
            try:
                self._wait_for_operation(operation=operation, timeout=timeout)
                logger.info(f"Operation '{operation.name}' completed successfully.")
            except Exception as error:
                raise RuntimeError(
                    f"Failed to wait for operation '{operation.name}' "
                    f"on instance '{instance_name}': {error}"
                ) from error

        logger.info(
            f"All ongoing update operations "
            f"for instance '{instance_name}' have completed."
        )
        return True

    def _modify_instance_activation_policy(
        self,
        instance_name: str,
        new_activation_policy: ActivationPolicy,
        sync: bool,
        timeout: int = 600,
    ):
        instance = self.get_instance_by_name(instance_name)
        if instance is None:
            raise ValueError(f"Instance '{instance_name}' does not exist.")

        try:
            operation = Operation(
                **(
                    # pylint: disable=no-member
                    self.client.instances()
                    .patch(
                        project=self.project_id,
                        instance=instance_name,
                        body=InstancePatchBody(
                            settings=Settings(activationPolicy=new_activation_policy)
                        ).dict(),
                    )
                    .execute()
                )
            )
            if sync:
                self._wait_for_operation(operation, timeout=timeout)
                logger.info(f"Instance '{instance_name}' policy has been modified.")
        except HttpError as http_error:
            logger.error(
                f"Failed to modify instance '{instance_name} policy': {http_error}"
            )
            raise

    def stop_instance(self, instance_name: str, sync: bool = True):
        """
        Stop a Cloud SQL instance.
        """
        try:
            self._modify_instance_activation_policy(
                instance_name=instance_name,
                new_activation_policy=ActivationPolicy.NEVER,
                sync=sync,
            )
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
        try:
            self._modify_instance_activation_policy(
                instance_name=instance_name,
                new_activation_policy=ActivationPolicy.ALWAYS,
                sync=sync,
            )
        except HttpError as http_error:
            logger.error(f"Failed to start instance '{instance_name}': {http_error}")
            raise
