from __future__ import annotations

import os

import groundingdino
import requests
from core.packages.abstract.online_prediction_model.modules.model import (
    OnlinePredictionModel,
)
from core.schemas.detect_anything import (
    DetectAnythingImagePredictions,
    DetectAnythingPrediction,
)
from groundingdino.util.inference import load_model, predict


def download_file(url, filename, chunk_size: int = 8192, timeout: int = 120):
    """Download a file from a given URL to a specified filename."""
    response = requests.get(url, stream=True, timeout=timeout)
    if response.status_code == 200:
        with open(filename, "wb") as file:
            for chunk in response.iter_content(chunk_size=chunk_size):
                file.write(chunk)


class DetectAnythingModel(OnlinePredictionModel):
    PRETRAINED_WEIGHTS_URL = (
        "https://github.com/IDEA-Research/GroundingDINO/releases"
        "/download/v0.1.0-alpha/groundingdino_swint_ogc.pth"
    )

    def __init__(
        self,
        # model_type: str,
        # model_name: str,
        *args,
        **kwargs,
    ):
        # self.model_type = model_type
        # self.model_name = model_name
        super().__init__(*args, **kwargs)

    @classmethod
    def get_pretrained_weights_filename(cls) -> str:
        pretrained_weights_filename = "~/.cache/neuronest/detect-anything/"
        pretrained_weights_filename += (
            cls.PRETRAINED_WEIGHTS_URL.replace("http://", "")
            .replace("https://", "")
            .replace("/", "_")
        )

        return os.path.expanduser(pretrained_weights_filename)

    # pylint: disable=arguments-differ
    def __call__(
        self,
        image,
        text_prompt,
        box_threshold: float = 0.35,
        text_threshold: float = 0.25,
        device: str = "cuda",
    ) -> DetectAnythingImagePredictions:
        boxes, logits, phrases = predict(
            model=self._model,
            image=image,
            caption=text_prompt,
            box_threshold=box_threshold,
            text_threshold=text_threshold,
            device=device,
        )

        return DetectAnythingImagePredictions(
            predictions=[
                DetectAnythingPrediction(bbox=bbox, logit=logit, phrase=phrase)
                for bbox, logit, phrase in zip(boxes, logits, phrases)
            ]
        )

    def retrieve_remote_model(self, pretrained: bool = False, device: str = "cuda"):
        if not pretrained:
            raise NotImplementedError

        if not os.path.exists(self.get_pretrained_weights_filename()):
            # Ensure the directory for the file exists
            os.makedirs(
                os.path.dirname(self.get_pretrained_weights_filename()), exist_ok=True
            )

            # Download the file if it does not exist
            print("Downloading the file...")
            download_file(
                self.PRETRAINED_WEIGHTS_URL, self.get_pretrained_weights_filename()
            )
            print("Download complete.")

        return load_model(
            model_config_path=os.sep.join(
                [
                    os.path.dirname(groundingdino.__file__),
                    "config",
                    "GroundingDINO_SwinT_OGC.py",
                ]
            ),
            model_checkpoint_path=self.get_pretrained_weights_filename(),
            device=device,
        )
        # return self._load_hub_model(
        #     model_type=self.model_type,
        #     model_name=self.model_name,
        #     pretrained=pretrained,
        # )

    def fit(self, *args, **kwargs):
        # pylint: disable=attribute-defined-outside-init
        self._model = self.retrieve_remote_model(pretrained=True)
