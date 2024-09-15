from enum import Enum
from typing import Optional, Type, Union

import numpy as np
from pydantic import BaseModel

from core.google.storage_client import StorageClient


class JobResultsType(str, Enum):
    JSON = "json"
    NUMPY_ARRAY = "numpy_array"


class JobResultsManager:
    def __init__(self, storage_client: StorageClient, bucket_name: str):
        self.storage_client = storage_client
        self.bucket_name = bucket_name

    def store_results(self, results_id: str, results: Union[BaseModel, np.ndarray]):
        if isinstance(results, BaseModel):
            self.storage_client.upload_blob_from_dict(
                bucket_name=self.bucket_name,
                blob_name=results_id,
                content=results.dict(),
            )
            return

        if isinstance(results, np.ndarray):
            self.storage_client.upload_blob_from_array(
                bucket_name=self.bucket_name, blob_name=results_id, content=results
            )

        raise NotImplementedError(f"Not supported type: {type(results)}")

    def retrieve_results(
        self,
        results_id: str,
        job_results_type: JobResultsType,
        results_pydantic_class: Optional[Type[BaseModel]],
    ) -> Union[BaseModel, np.ndarray]:
        if job_results_type == JobResultsType.JSON:
            content = self.storage_client.download_blob(
                bucket_name=self.bucket_name, blob_name=results_id, as_json=True
            )

            return results_pydantic_class.parse_obj(content)

        if job_results_type == JobResultsType.NUMPY_ARRAY:
            return self.storage_client.download_blob_as_array(
                bucket_name=self.bucket_name, blob_name=results_id
            )

        raise NotImplementedError(f"Not supported type: {job_results_type}")
