import logging

from core.google.cloud_run_job_manager import CloudRunJobManager
from core.google.cloud_sql_manager import CloudSQLManager
from core.google.utils import fetch_active_service_account_email
from core.google.vertex_ai_manager import VertexAIManager
from core.routes.model_instantiator import routes
from core.schemas.google.cloud_run import JobConfig
from core.schemas.model_instantiator import (
    CloudSQL,
    CloudSQLOutput,
    InstantiateModelInput,
    InstantiateModelOutput,
)
from core.utils import underscore_to_hyphen
from fastapi import APIRouter, Depends, Response
from omegaconf import DictConfig
from starlette import status

from model_instantiator.api.dependencies import (
    use_cloud_run_job_manager,
    use_cloud_sql_manager,
    use_config,
    use_vertex_ai_manager,
)
from model_instantiator.environment_variables import PROJECT_ID, REGION

router = APIRouter(
    prefix=f"/{routes.Instantiator.prefix}", tags=[routes.Instantiator.prefix]
)


def _already_deployed_endpoint_response(
    response: Response, model_name: str
) -> InstantiateModelOutput:
    response.status_code = status.HTTP_200_OK

    return InstantiateModelOutput(
        message=f"Endpoint already deployed for model_name: '{model_name}'"
    )


def _already_running_job_response(
    response: Response, job_name: str
) -> InstantiateModelOutput:
    response.status_code = status.HTTP_200_OK

    return InstantiateModelOutput(
        message=f"A deployment job is already running for job: '{job_name}'"
    )


def _deploying_endpoint_response(
    response: Response, model_name: str
) -> InstantiateModelOutput:
    response.status_code = status.HTTP_201_CREATED

    return InstantiateModelOutput(
        message=f"Endpoint being deployed for model_name: '{model_name}', "
        f"or is already deploying"
    )


def _no_model_response(response: Response, model_name: str) -> InstantiateModelOutput:
    response.status_code = status.HTTP_404_NOT_FOUND

    return InstantiateModelOutput(
        message=f"No vertex model found with name: '{model_name}'"
    )


@router.post(routes.Instantiator.instantiate, status_code=status.HTTP_201_CREATED)
def instantiate_model(
    instantiate_model_input: InstantiateModelInput,
    response: Response,
    config: DictConfig = Depends(use_config),
    vertex_ai_manager: VertexAIManager = Depends(use_vertex_ai_manager),
    cloud_run_job_manager: CloudRunJobManager = Depends(use_cloud_run_job_manager),
):
    model_name = instantiate_model_input.model_name

    model = vertex_ai_manager.get_last_model_by_name(name=model_name)

    if model is None:
        return _no_model_response(response=response, model_name=model_name)

    if vertex_ai_manager.is_model_deployed(name=model_name, model=model):
        return _already_deployed_endpoint_response(
            response=response, model_name=model_name
        )

    job_name = f"model-{underscore_to_hyphen(instantiate_model_input.model_name)}"
    execution = cloud_run_job_manager.list_executions(job_name, exclude_terminated=True)

    if len(execution) > 0:
        return _already_running_job_response(response=response, job_name=job_name)

    cloud_run_job_manager.create_job(
        job_name=job_name,
        job_config=JobConfig(
            container_uri=config.job.container_uri,
            cpu=config.job.cpu,
            memory=config.job.memory,
            command=["python"],
            command_args=[
                "-m",
                "model_instantiator.jobs.deploy_model",
            ],
            environment_variables={
                "PROJECT_ID": PROJECT_ID,
                "REGION": REGION,
                "MODEL_NAME": model_name,
            },
        ),
        override_if_existing=True,
    )
    cloud_run_job_manager.run_job(job_name=job_name)

    return _deploying_endpoint_response(response=response, model_name=model_name)


def _no_instance_response(response: Response, instance_name: str):
    response.status_code = status.HTTP_404_NOT_FOUND
    return CloudSQLOutput(message=f"Cloud SQL instance '{instance_name}' not found.")


def _already_running_instance_response(response: Response, instance_name: str):
    response.status_code = status.HTTP_200_OK
    return CloudSQLOutput(
        message=f"Cloud SQL instance '{instance_name}' is already running."
    )


def _already_starting_instance_response(response: Response, instance_name: str):
    response.status_code = status.HTTP_200_OK
    return CloudSQLOutput(
        message=f"Cloud SQL instance '{instance_name}' is already starting."
    )


def _starting_instance_response(
    response: Response, instance_name: str, status_code: int = status.HTTP_200_OK
):
    response.status_code = status_code
    return CloudSQLOutput(message=f"Cloud SQL instance '{instance_name}' is starting.")


@router.post(
    routes.Instantiator.instantiate_cloud_sql, status_code=status.HTTP_201_CREATED
)
def instantiate_cloud_sql_instance(
    instantiate_cloud_sql_input: CloudSQL,
    response: Response,
    cloud_run_job_config: DictConfig = Depends(use_config),
    cloud_sql_manager: CloudSQLManager = Depends(use_cloud_sql_manager),
    cloud_run_job_manager: CloudRunJobManager = Depends(use_cloud_run_job_manager),
):
    instance_name = instantiate_cloud_sql_input.instance_name
    logging.info(f"Received request to start Cloud SQL instance: {instance_name}")

    # Fetch the instance details
    instance = cloud_sql_manager.get_instance_by_name(instance_name)

    if instance is None:
        logging.warning(f"Instance {instance_name} not found.")
        return _no_instance_response(response=response, instance_name=instance_name)

    # Check if the instance is already running
    if cloud_sql_manager.is_instance_started(instance_name):
        logging.info(f"Instance {instance_name} is already running.")
        return _already_running_instance_response(
            response=response,
            instance_name=instance_name,
        )

    # Check if the instance is already starting
    if cloud_sql_manager.is_instance_starting(instance_name):
        logging.info(f"Instance {instance_name} is already starting.")
        return _already_starting_instance_response(
            response=response, instance_name=instance_name
        )

    job_name = f"cloudsql-{underscore_to_hyphen(instance_name)}"

    # Check if a job execution is already running
    execution = cloud_run_job_manager.list_executions(job_name, exclude_terminated=True)
    if len(execution) > 0:
        logging.info(
            f"Job execution already running for {job_name}. Skipping new job creation."
        )
        return _already_running_job_response(response=response, job_name=job_name)

    active_service_account_email = fetch_active_service_account_email()
    logging.info(
        f"Using service account: {active_service_account_email} "
        f"for Cloud Run job: {job_name}"
    )

    # Create and start the Cloud Run job
    logging.info(f"Creating Cloud Run job: {job_name} with instance: {instance_name}")
    cloud_run_job_manager.create_job(
        job_name=job_name,
        job_config=JobConfig(
            container_uri=cloud_run_job_config.job.container_uri,
            cpu=cloud_run_job_config.job.cpu,
            memory=cloud_run_job_config.job.memory,
            command=["python"],
            command_args=[
                "-m",
                "model_instantiator.jobs.start_cloud_sql_instance",
            ],
            environment_variables={
                "CLOUD_SQL_INSTANCE_NAME": instance_name,
            },
        ),
        override_if_existing=True,
        service_account=active_service_account_email,
    )

    logging.info(f"Starting Cloud Run job: {job_name}")
    cloud_run_job_manager.run_job(job_name=job_name)

    return _starting_instance_response(
        response=response,
        instance_name=instance_name,
        status_code=status.HTTP_202_ACCEPTED,
    )
