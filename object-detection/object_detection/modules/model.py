from __future__ import annotations

from typing import List

import pandas as pd
import torch
from core.packages.abstract.online_prediction_model.modules.model import (
    OnlinePredictionModel,
)


class ObjectDetectionModel(OnlinePredictionModel):
    def __init__(
        self,
        model_type: str,
        model_name: str,
        # model_tag: str,
        *args,
        **kwargs,
        # model_extension: str = ".pt",
        # retrieve_remote_model: bool = False,
    ):
        self.model_type = model_type
        self.model_name = model_name
        # self.model_tag = model_tag
        super().__init__(*args, **kwargs)
        # self.model_extension = model_extension
        #
        # self._model: Optional[nn.Module] = None
        # if retrieve_remote_model:
        #     # self._model = self._load_hub_pretrained_model()
        #     self._model = self._retrieve_remote_model()

    # @abstractmethod
    # def __call__(self, *args, **kwargs) -> List[pd.DataFrame]:
    #     raise NotImplementedError

    # def _load_hub_pretrained_model(self):
    #     return torch.hub.load(self.model_type, self.model_name, pretrained=True)

    # @abstractmethod
    # def _retrieve_remote_model(self):
    #     raise NotImplementedError

    # @abstractmethod
    # def fit(self, *args, **kwargs):
    #     raise NotImplementedError

    def __call__(self, *args, **kwargs) -> List[pd.DataFrame]:
        # noinspection PyCallingNonCallable
        predictions = self._model(*args, **kwargs)

        return list(predictions.pandas().xyxy)

    def _retrieve_remote_model(self, pretrained: bool = False):
        return torch.hub.load(self.model_type, self.model_name, pretrained=pretrained)

    # def _load_hub_pretrained_model(self):
    #     return self._load_hub_model(pretrained=True)

    def fit(self, *args, **kwargs):
        # pylint: disable=attribute-defined-outside-init
        self._model = self._retrieve_remote_model(pretrained=True)

    #
    # def eval(self):
    #     return self._model.eval()
    #
    # def save(self, path: str):
    #     torch.save(self._model, path)
    #
    # def save_on_gcs(
    #     self,
    #     storage_client: StorageClient,
    #     directory_path: GSPath,
    #     weights_name: str = "model",
    # ):
    #     with tempfile.NamedTemporaryFile(
    #         suffix=self.model_extension
    #     ) as named_temporary_file:
    #         self.save(named_temporary_file.name)
    #
    #         bucket_name, directory_name = directory_path.to_bucket_and_blob_names()
    #         blob_name = os.path.join(
    #             directory_name, weights_name + self.model_extension
    #         )
    #
    #         storage_client.upload_blob(
    #             source_file_name=named_temporary_file.name,
    #             bucket_name=bucket_name,
    #             blob_name=blob_name,
    #         )

    def load(self, path: str) -> ObjectDetectionModel:
        # loads in memory the project architecture of the model so that it is visible
        # to the interpreter when loading the MODEL.pt
        self._retrieve_remote_model(pretrained=False)
        self._model = torch.load(path)
        return self
