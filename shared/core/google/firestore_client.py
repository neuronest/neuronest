import logging
from typing import Any, List, Optional, Union

from google.cloud import firestore
from google.cloud.firestore_v1 import DocumentReference, Transaction

from core.serialization.encoding import json_encodable_dict

logger = logging.getLogger(__name__)


class FirestoreClient:
    def __init__(self, key_path: Optional[str] = None):
        self.client = (
            firestore.Client()
            if key_path is None
            else firestore.Client.from_service_account_json(key_path)
        )

    def upload_document(self, collection_name: str, document_id: str, content: dict):
        doc_ref = self.client.collection(collection_name).document(document_id)
        doc_ref.set(json_encodable_dict(content))

        logger.info(
            f"Document '{document_id}' uploaded to collection '{collection_name}'"
        )

    def get_document(
        self,
        collection_name: str,
        document_id: str,
    ) -> Optional[Union[dict, Any]]:
        document = self.client.collection(collection_name).document(document_id).get()

        if not document.exists:
            logger.info(
                f"No results for document '{document_id}' in collection "
                f"'{collection_name}'"
            )
            return None

        logger.info(
            f"Results for document '{document_id}' in collection '{collection_name}' "
            f"retrieved"
        )

        return document.to_dict()

    @staticmethod
    @firestore.transactional
    def _update_in_transaction(
        transaction: Transaction,
        document_reference: DocumentReference,
        fields: List[str],
        new_values: List[Union[str, int, float, bool]],
    ):
        transaction.update(
            document_reference, json_encodable_dict(dict(zip(fields, new_values)))
        )

    def update_document(
        self,
        collection_name: str,
        document_id: str,
        fields: List[str],
        new_values: List[Union[str, int, float, bool]],
    ):
        if len(fields) != len(new_values):
            raise ValueError(
                "The number of fields should be equal to the number of new values"
            )

        document = self.client.collection(collection_name).document(document_id)

        self._update_in_transaction(
            transaction=self.client.transaction(),
            document_reference=document,
            fields=fields,
            new_values=new_values,
        )

        logger.info(
            f"The following fields of the document '{document_id}' in the collection "
            f"'{collection_name}' has been updated: {' '.join(fields)}"
        )

    def delete_document(self, collection: str, document_id: str):
        document = self.client.collection(collection).document(document_id)
        document.delete()

        logger.info(f"Document '{document_id}' deleted in collection '{collection}'")
