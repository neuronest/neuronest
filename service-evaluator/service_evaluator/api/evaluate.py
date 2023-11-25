import uuid
from datetime import datetime
from typing import Optional

from core.api_exceptions import abort
from core.google.firestore_client import FirestoreClient
from core.google.vertex_ai_manager import VertexAIManager
from core.routes.service_evaluator import routes
from core.schemas.image_name import ImageName
from core.schemas.service_evaluator import (
    EvaluatedServiceName,
    EvaluateJobDocument,
    ServiceEvaluatorInput,
    ServiceEvaluatorOutput,
)
from core.utils import underscore_to_hyphen
from fastapi import APIRouter, Depends, Response, status
from google.cloud import aiplatform
from omegaconf import DictConfig

from service_evaluator.api.dependencies import (
    use_config,
    use_firestore_client,
    use_firestore_jobs_collection,
    use_job_prefix_name,
    use_service_image_name,
    use_service_name,
    use_vertex_ai_manager,
)
from service_evaluator.environment_variables import (
    PROJECT_ID,
    REGION,
    SERIALIZED_SERVICE_CLIENT_PARAMETERS,
)

router = APIRouter(prefix=f"/{routes.Evaluator.prefix}", tags=[routes.Evaluator.prefix])


def _already_running_job_response(
    response: Response, job_id: str
) -> ServiceEvaluatorOutput:
    response.status_code = status.HTTP_200_OK

    return ServiceEvaluatorOutput(
        job_id=job_id,
    )


def _launched_job_response(
    response: Response,
    job_id: str,
) -> ServiceEvaluatorOutput:
    response.status_code = status.HTTP_201_CREATED

    return ServiceEvaluatorOutput(
        job_id=job_id,
    )


def _upload_evaluate_job_document(
    firestore_client: FirestoreClient,
    firestore_jobs_collection: str,
    job_id: str,
    service_name: EvaluatedServiceName,
    image_name: ImageName,
):
    people_job_document = EvaluateJobDocument(
        job_id=job_id,
        job_date=datetime.utcnow(),
        service_name=service_name,
        image_name=image_name,
    )
    firestore_client.upload_document(
        collection_name=firestore_jobs_collection,
        document_id=job_id,
        content=people_job_document.dict(),
    )


def _download_last_evaluate_job_document(
    firestore_client: FirestoreClient,
    firestore_jobs_collection: str,
    service_name: EvaluatedServiceName,
) -> Optional[EvaluateJobDocument]:
    documents = firestore_client.get_documents_based_on_condition(
        collection_name=firestore_jobs_collection,
        field_name="service_name",
        field_value=service_name,
        desc_order_by_field="job_date",
    )

    if len(documents) == 0:
        return None

    document = documents[0]

    return EvaluateJobDocument.parse_obj(document)


@router.post(routes.Evaluator.evaluate, status_code=status.HTTP_201_CREATED)
def evaluate(
    service_evaluator_input: ServiceEvaluatorInput,
    response: Response,
    config: DictConfig = Depends(use_config),
    vertex_ai_manager: VertexAIManager = Depends(use_vertex_ai_manager),
    firestore_client: FirestoreClient = Depends(use_firestore_client),
    firestore_jobs_collection: str = Depends(use_firestore_jobs_collection),
    service_name: EvaluatedServiceName = Depends(use_service_name),
    job_prefix_name: str = Depends(use_job_prefix_name),
    service_image_name: ImageName = Depends(use_service_image_name),
):
    job_name = underscore_to_hyphen(f"{job_prefix_name}-{service_name}")

    running_jobs = vertex_ai_manager.list_training_pipelines(
        exclude_terminated=True, display_name_filter=job_name
    )

    if len(running_jobs) > 0:
        last_evaluate_job_document = _download_last_evaluate_job_document(
            firestore_client=firestore_client,
            firestore_jobs_collection=firestore_jobs_collection,
            service_name=service_name,
        )

        if last_evaluate_job_document is None:
            abort(
                code=500,
                detail=f"A job is apparently running but no trace of it in the "
                f"database (service_name={service_name})",
            )

        return _already_running_job_response(
            response=response, job_id=last_evaluate_job_document.job_id
        )

    job_id = uuid.uuid4().hex

    _upload_evaluate_job_document(
        firestore_client=firestore_client,
        firestore_jobs_collection=firestore_jobs_collection,
        job_id=job_id,
        service_name=service_name,
        image_name=service_image_name,
    )

    job = aiplatform.CustomContainerTrainingJob(
        display_name=job_name,
        location=vertex_ai_manager.location,
        container_uri=config.job.container_uri,
        command=["python", "-m", f"{config.package_name}.jobs.evaluate"],
    )

    job.run(
        service_account=config.service_account,
        machine_type=config.machine_type,
        sync=False,
        environment_variables={
            "REUSE_ALREADY_COMPUTED_RESULTS": (
                service_evaluator_input.reuse_already_computed_results
            ),
            "PROJECT_ID": PROJECT_ID,
            "REGION": REGION,
            "SERIALIZED_SERVICE_CLIENT_PARAMETERS": (
                SERIALIZED_SERVICE_CLIENT_PARAMETERS
            ),
            "SERVICE_NAME": service_name,
        },
    )

    return _launched_job_response(
        response=response,
        job_id=job_id,
    )
