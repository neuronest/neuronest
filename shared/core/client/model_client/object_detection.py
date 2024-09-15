from typing import List, cast

import pandas as pd
from imutils import resize

from core.client.model_client.abstract.online_prediction_model import (
    OnlinePredictionModelClient,
)
from core.schemas.abstract.online_prediction_model import InputSampleSchema
from core.schemas.object_detection import (
    InputSampleSchema as ObjectDetectionInputSampleSchema,
)
from core.schemas.object_detection import (
    OutputSampleSchema as ObjectDetectionOutputSampleSchema,
)


class ObjectDetectionClient(OnlinePredictionModelClient):
    INPUT_SAMPLE_SCHEMA = ObjectDetectionInputSampleSchema
    OUTPUT_SAMPLE_SCHEM = ObjectDetectionOutputSampleSchema
    MAX_SIZE = (640, 640)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @staticmethod
    def _are_shapes_correct(samples: List[ObjectDetectionInputSampleSchema]) -> bool:
        if any(
            sample.image.ndim not in (2, 3)
            or sample.image.ndim == 3
            and sample.image.shape[2] != 3
            for sample in samples
        ):
            return False

        return True

    def _resize_images(
        self, samples: List[ObjectDetectionInputSampleSchema]
    ) -> List[ObjectDetectionInputSampleSchema]:
        """
        If any dimension of an image if greater than self.MAX_SIZE (width, height),
        then the image is going to be resized without changing the ratio,
        with self.MAX_SIZE being the maximum.
        """
        return [
            ObjectDetectionInputSampleSchema(
                image=resize(
                    image=sample.image,
                    height=self.MAX_SIZE[0]
                    if sample.image.shape[0] > self.MAX_SIZE[0]
                    and sample.image.shape[0] > sample.image.shape[1]
                    else None,
                    width=self.MAX_SIZE[1]
                    if sample.image.shape[1] > self.MAX_SIZE[1]
                    and sample.image.shape[1] > sample.image.shape[0]
                    else None,
                ),
                labels_to_predict=sample.labels_to_predict,
                confidence_threshold=sample.confidence_threshold,
                overridden_image_width=sample.overridden_image_width,
            )
            for sample in samples
        ]

    # pylint: disable=arguments-differ,arguments-renamed
    def predict_batch(
        self,
        samples: List[InputSampleSchema],
    ) -> List[pd.DataFrame]:
        samples = cast(List[ObjectDetectionInputSampleSchema], samples)
        if not self._are_shapes_correct(samples):
            raise ValueError("Incorrect received shapes")

        return super().predict_batch(samples=self._resize_images(samples))
