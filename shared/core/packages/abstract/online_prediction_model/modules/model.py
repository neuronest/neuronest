from __future__ import annotations

import os
import tempfile
from abc import ABC, abstractmethod
from typing import Any, List, Optional

import torch
from torch import nn

from core.google.storage_client import StorageClient
from core.path import GSPath


class OnlinePredictionModel(ABC):
    def __init__(
        self,
        model_extension: str = ".pt",
        retrieve_remote_model: bool = False,
    ):
        self.model_extension = model_extension

        self._model: Optional[nn.Module] = None
        if retrieve_remote_model:
            self._model = self._retrieve_remote_model(pretrained=True)

    @abstractmethod
    def __call__(self, *args, **kwargs) -> List[Any]:
        raise NotImplementedError

    @abstractmethod
    def _retrieve_remote_model(self, pretrained: bool = False):
        raise NotImplementedError

    @abstractmethod
    def fit(self, *args, **kwargs):
        raise NotImplementedError

    @staticmethod
    def _load_hub_model(model_type: str, model_name: str, pretrained: bool = False):
        return torch.hub.load(model_type, model_name, pretrained=pretrained)

    # pylint: disable=invalid-name
    def to(self, device: str):
        self._model.to(device)

    def eval(self):
        return self._model.eval()

    def save(self, path: str):
        torch.save(self._model, path)

    def save_on_gcs(
        self,
        storage_client: StorageClient,
        directory_path: GSPath,
        weights_name: str = "model",
    ):
        with tempfile.NamedTemporaryFile(
            suffix=self.model_extension
        ) as named_temporary_file:
            self.save(named_temporary_file.name)

            bucket_name, directory_name = directory_path.to_bucket_and_blob_names()
            blob_name = os.path.join(
                directory_name, weights_name + self.model_extension
            )

            storage_client.upload_blob(
                source_file_name=named_temporary_file.name,
                bucket_name=bucket_name,
                blob_name=blob_name,
            )

    def load(self, path: str) -> OnlinePredictionModel:
        # loads in memory the project architecture of the model so that it is visible
        # to the interpreter when loading the MODEL.pt
        self._retrieve_remote_model(pretrained=False)
        self._model = torch.load(path)
        return self
