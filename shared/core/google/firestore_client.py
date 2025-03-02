import logging
import time
from typing import Any, List, Optional, Union

from google.api_core.exceptions import Conflict, GoogleAPICallError
from google.cloud import firestore
from google.cloud.firestore_v1 import DocumentReference, Transaction

from core.client.abstract.base_client import BaseClient
from core.serialization.encoding import json_encodable_dict

logger = logging.getLogger(__name__)


class FirestoreClient(BaseClient):
    def __init__(
        self, key_path: Optional[str] = None, project_id: Optional[str] = None
    ):
        super().__init__(key_path=key_path, project_id=project_id)
        # noinspection PyTypeChecker
        self.client = (
            firestore.Client(project=self.project_id)
            if key_path is None
            else firestore.Client.from_service_account_json(
                json_credentials_path=key_path, project=self.project_id
            )
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

    def acquire_lock(self, lock_name: str, timeout: int) -> bool:
        doc_ref = self.client.collection("locks").document(lock_name)

        transaction = self.client.transaction()  # Explicitly create a transaction

        @firestore.transactional
        def transaction_logic(txn):
            """Runs inside Firestore transaction."""
            doc = doc_ref.get(transaction=txn)  # Read inside transaction
            now = time.time()

            # Lock acquisition logic
            if not doc.exists or now - doc.get("timestamp") > timeout:
                txn.set(doc_ref, {"timestamp": now})  # Write inside transaction
                return True  # Lock acquired
            return False  # Lock not acquired

        try:
            return transaction_logic(transaction)
        except Conflict:
            print(
                f"Lock acquisition conflict on '{lock_name}'. Another process holds it."
            )
        except GoogleAPICallError as e:
            print(f"Firestore API error while acquiring lock '{lock_name}': {e}")
        except ValueError as e:
            print(f"Transaction error: {e}")  # Handle inactive transaction case
        return False  # Lock not acquired

    def release_lock(self, lock_name: str):
        self.delete_document(collection="locks", document_id=lock_name)
