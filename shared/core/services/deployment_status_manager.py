import datetime
import logging
from enum import Enum
from typing import Optional, Union

from google.cloud import firestore
from google.cloud.firestore_v1 import DocumentReference, Transaction
from pydantic import BaseModel

from core.google.firestore_client import FirestoreClient
from core.serialization.encoding import json_encodable_dict

logger = logging.getLogger(__name__)


class DeploymentStatus(str, Enum):
    DEPLOYED = "deployed"
    DEPLOYING = "deploying"
    UNDEPLOYED = "undeployed"
    FAILED = "failed"


class DeploymentStatusDocument(BaseModel):
    deployment_status: DeploymentStatus
    created_date: datetime.datetime = datetime.datetime.now()


class DeploymentStatusManager:
    def __init__(
        self,
        firestore_client: FirestoreClient,
        collection_name: str,
        max_deploying_age: int,
        default_deployment_name: Optional[str] = None,
    ):
        self.firestore_client = firestore_client
        self.collection_name = collection_name
        self.max_deploying_age = max_deploying_age  # in seconds
        self.default_deployment_name = default_deployment_name

    def _infer_deployment_name(self, deployment_name: Optional[str]) -> str:
        deployment_name = deployment_name or self.default_deployment_name

        if deployment_name is None:
            raise ValueError(
                "Either default_deployment_name or deployment_name should be specified"
            )

        return deployment_name

    @staticmethod
    @firestore.transactional
    def _maybe_set_status(
        transaction: Transaction,
        document_reference: DocumentReference,
        deployment_status: DeploymentStatus,
        max_deploying_age: int,
    ) -> Optional[DeploymentStatusDocument]:
        raw_deployment_status_snapshot = document_reference.get(
            transaction=transaction
        ).to_dict()
        new_deployment_status_document = DeploymentStatusDocument(
            deployment_status=deployment_status
        )

        if raw_deployment_status_snapshot is None:
            transaction.create(
                document_reference,
                json_encodable_dict(new_deployment_status_document.dict()),
            )
            return new_deployment_status_document

        deployment_status_snapshot = DeploymentStatusDocument.parse_obj(
            raw_deployment_status_snapshot
        )
        if (
            deployment_status_snapshot.deployment_status == DeploymentStatus.DEPLOYING
            and datetime.datetime.now() - datetime.timedelta(seconds=max_deploying_age)
            < deployment_status_snapshot.created_date
        ):
            return None

        transaction.update(
            document_reference,
            json_encodable_dict(new_deployment_status_document.dict()),
        )

        return new_deployment_status_document

    def maybe_set_status(
        self,
        deployment_status: Union[DeploymentStatus, str],
        deployment_name: Optional[str] = None,
    ) -> Optional[DeploymentStatusDocument]:
        document = self.firestore_client.client.collection(
            self.collection_name
        ).document(self._infer_deployment_name(deployment_name))

        deployment_status_document = self._maybe_set_status(
            transaction=self.firestore_client.client.transaction(),
            document_reference=document,
            deployment_status=deployment_status,
            max_deploying_age=self.max_deploying_age,
        )

        return deployment_status_document

    def get_status(
        self, missing_ok: bool = True, deployment_name: Optional[str] = None
    ) -> DeploymentStatusDocument:
        deployment_status = self.firestore_client.get_document(
            self.collection_name, self._infer_deployment_name(deployment_name)
        )

        if deployment_status is None and missing_ok:
            deployment_status_document = self.maybe_set_status(
                deployment_status=DeploymentStatus.UNDEPLOYED,
                deployment_name=deployment_name,
            )

            return deployment_status_document

        return DeploymentStatusDocument.parse_obj(deployment_status)
