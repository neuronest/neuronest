from core.google.cloud_run_job_manager import CloudRunJobManager
from core.google.vertex_ai_manager import VertexAIManager
from core.routes.model_instantiator import routes
from core.schemas.google.cloud_run import JobConfig
from core.schemas.model_instantiator import (
    InstantiateModelInput,
    InstantiateModelOutput,
)
from core.utils import underscore_to_hyphen
from fastapi import APIRouter, Depends, Response
from omegaconf import DictConfig
from starlette import status

from model_instantiator.api.dependencies import (
    use_cloud_run_job_manager,
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
    response: Response, model_name: str
) -> InstantiateModelOutput:
    response.status_code = status.HTTP_200_OK

    return InstantiateModelOutput(
        message=f"A deployment job is already running for model_name: '{model_name}'"
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

    job_name = underscore_to_hyphen(instantiate_model_input.model_name)
    execution = cloud_run_job_manager.list_executions(job_name, exclude_terminated=True)

    if len(execution) > 0:
        return _already_running_job_response(response=response, model_name=model_name)

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
