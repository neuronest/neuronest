from __future__ import annotations

from typing import List, Optional

import numpy as np
from PIL import Image

from core.schemas.abstract import online_prediction_model
from core.serialization.schema import Schema

INPUT_SAMPLE_SCHEMA_IMAGE_TYPE_SERIALIZATION = ".jpg"


class DetectAnythingPredictionBbox(Schema):
    min_x: int
    min_y: int
    max_x: int
    max_y: int
    relative_min_x: Optional[float]
    relative_min_y: Optional[float]
    relative_max_x: Optional[float]
    relative_max_y: Optional[float]


class DetectAnythingPrediction(Schema):
    bbox: DetectAnythingPredictionBbox
    logit: np.ndarray
    phrase: str


class DetectAnythingImagePredictions(Schema):
    predictions: List[DetectAnythingPrediction]
    annotated_image: Optional[Image.Image]


class InputSampleSchema(Schema):
    rgb_image: np.ndarray
    texts_prompt: List[str]
    box_threshold: float
    text_threshold: float
    annotate_image: bool = False


class OutputSampleSchema(online_prediction_model.OutputSampleSchema):
    results: DetectAnythingImagePredictions
