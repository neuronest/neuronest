from __future__ import annotations

from typing import Optional, Union

import torch
from core.packages.abstract.online_prediction_model.modules.model import (
    OnlinePredictionModel,
)
from core.schemas.abstract.online_prediction_model import Device
from core.schemas.video_comparator import PredictionType

from video_comparator.model.visil import ViSiL
from video_comparator.utils import extract_features
from video_comparator.utils import load_video as visil_video_load


class VideoComparatorModel(OnlinePredictionModel):
    def __init__(
        self,
        # model_type: str,
        # model_name: str,
        # model_tag: str,
        # *args,
        # **kwargs,
        # model_extension: str = ".pt",
        # retrieve_remote_model: bool = False,
    ):
        print()
        # self.model_type = model_type
        # self.model_name = model_name
        # self.model_tag = model_tag
        super().__init__()
        # self.model_extension = model_extension
        #
        # self._model: Optional[nn.Module] = None
        # if retrieve_remote_model:
        #     # self._model = self._load_hub_pretrained_model()
        #     self._model = self._retrieve_remote_model()

    # pylint: disable=arguments-differ
    def __call__(
        self,
        video_path: str,
        other_video_path: Optional[str] = None,
        prediction_type: str = PredictionType.SIMILARITY,
        device: Device = Device.CUDA,
        batch_size: int = 128,
    ) -> Union[torch.Tensor, float]:
        video_features = extract_features(
            model=self._model,
            frames=torch.from_numpy(visil_video_load(video_path)),
            device=device,
            batch_sz=batch_size,
        )
        if prediction_type == PredictionType.VIDEO_FEATURES:
            return video_features
        other_video_features = extract_features(
            model=self._model,
            frames=torch.from_numpy(visil_video_load(other_video_path)),
            device=device,
            batch_sz=batch_size,
        )
        similarity = self._model.calculate_video_similarity(
            query=video_features, target=other_video_features
        )
        return similarity

    # @abstractmethod
    # def __call__(self, *args, **kwargs) -> List[pd.DataFrame]:
    #     raise NotImplementedError
    #
    # def _load_hub_pretrained_model(self):
    #     return torch.hub.load(self.model_type, self.model_name, pretrained=True)
    #
    def _retrieve_remote_model(self):
        visil = ViSiL(pretrained=True)
        visil.eval()
        return visil

    def fit(self, *args, **kwargs):
        # pylint: disable=attribute-defined-outside-init
        self._model = self._retrieve_remote_model()

    # def set_model(self, model):
    #     self._model = model

    # # pylint: disable=invalid-name
    # def to(self, device: str):
    #     self._model.to(device)

    # def eval(self):
    #     return self._model.eval()

    # def save(self, path: str):
    #     torch.save(self._model, path)

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
    #
