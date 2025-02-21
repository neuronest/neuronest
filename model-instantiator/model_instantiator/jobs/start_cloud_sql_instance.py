from typing import Optional

from core.google.cloud_sql_manager import CloudSQLManager

from model_instantiator.api.dependencies import use_cloud_sql_manager
from model_instantiator.jobs.environment_variables import CLOUD_SQL_INSTANCE_NAME


def start_cloud_sql_instance(
    instance_name: str,
    cloud_sql_manager: CloudSQLManager,
) -> Optional[dict]:
    instance = cloud_sql_manager.get_instance_by_name(instance_name)
    if instance is None:
        raise ValueError(f"Cloud SQL instance '{instance_name}' not found.")

    if cloud_sql_manager.is_instance_started(instance_name):
        return None
    if cloud_sql_manager.is_instance_stopping(instance_name):
        cloud_sql_manager.wait_for_instance_update(instance_name)
        if not cloud_sql_manager.is_instance_stopped(instance_name):
            raise RuntimeError(f"Failed to stop instance '{instance_name}'.")

    if not cloud_sql_manager.is_instance_starting(instance_name):
        cloud_sql_manager.start_instance(instance_name=instance_name, sync=True)

    if cloud_sql_manager.is_instance_started(instance_name):
        return None

    raise RuntimeError(f"Failed to start instance '{instance_name}'.")


if __name__ == "__main__":
    start_cloud_sql_instance(
        instance_name=CLOUD_SQL_INSTANCE_NAME,
        cloud_sql_manager=use_cloud_sql_manager(),
    )
