from __future__ import annotations

import os
import tempfile
from abc import ABC, abstractmethod
from typing import List, Optional

import pandas as pd
import torch
from torch import nn

from core.google.storage_client import StorageClient
from core.path import GSPath


class OnlinePredictionModel(ABC):
    def __init__(
        self,
        # model_type: str,
        # model_name: str,
        model_extension: str = ".pt",
        retrieve_remote_model: bool = False,
    ):
        # self.model_type = model_type
        # self.model_name = model_name
        self.model_extension = model_extension

        self._model: Optional[nn.Module] = None
        if retrieve_remote_model:
            # self._model = self._load_hub_pretrained_model()
            self._model = self._retrieve_remote_model()

    # def __call__(self, *args, **kwargs) -> List[pd.DataFrame]:
    #     # noinspection PyCallingNonCallable
    #     predictions = self._model(*args, **kwargs)
    #
    #     return list(predictions.pandas().xyxy)

    @abstractmethod
    def __call__(self, *args, **kwargs) -> List[pd.DataFrame]:
        raise NotImplementedError

    # def _load_hub_pretrained_model(self):
    #     return torch.hub.load(self.model_type, self.model_name, pretrained=True)

    @abstractmethod
    def _retrieve_remote_model(self):
        raise NotImplementedError

    @abstractmethod
    def fit(self, *args, **kwargs):
        raise NotImplementedError

    @staticmethod
    def get_model_pt_from_path(model_pt_path: str):
        return torch.load(model_pt_path)

    def set_model(self, model):
        self._model = model

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
        self._model = self.get_model_pt_from_path(path)
        return self
