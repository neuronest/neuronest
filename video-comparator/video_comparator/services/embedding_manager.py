from typing import List, Optional

import numpy as np
from core.exceptions import DependencyError
from core.google.storage_client import StorageClient


class EmbeddingManager:
    def __init__(self, storage_client: StorageClient, bucket_name: str):
        self.storage_client = storage_client
        self.bucket_name = bucket_name

    def store_embedding(self, asset_id: str, embedding: np.ndarray):
        self.storage_client.upload_blob_from_array(
            bucket_name=self.bucket_name, blob_name=asset_id, content=embedding
        )

    def store_multiple_embeddings(
        self, asset_ids: List[str], embeddings: List[np.ndarray]
    ):
        if len(asset_ids) != len(embeddings):
            raise ValueError(
                "The number of asset_ids should be equal to the number of embeddings"
            )

        for asset_id, embedding in zip(asset_ids, embeddings):
            self.storage_client.upload_blob_from_array(
                bucket_name=self.bucket_name, blob_name=asset_id, content=embedding
            )

    def retrieve_embedding(
        self, asset_id: str, is_missing_ok: bool = True
    ) -> Optional[np.ndarray]:
        try:
            return self.storage_client.download_blob_as_array(
                bucket_name=self.bucket_name, blob_name=asset_id
            )
        except DependencyError as dependency_error:
            if is_missing_ok is True:
                return None

            raise dependency_error

    def retrieve_multiple_embeddings(
        self, asset_ids: List[str], is_missing_ok: bool = True
    ) -> List[Optional[np.ndarray]]:
        return [
            self.retrieve_embedding(asset_id=asset_id, is_missing_ok=is_missing_ok)
            for asset_id in asset_ids
        ]
