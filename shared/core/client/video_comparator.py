from typing import Iterable, List, Union

import numpy as np

from core.client.abstract.online_prediction_model import OnlinePredictionModelClient
from core.google.storage_client import StorageClient
from core.path import GSPath
from core.schemas.video_comparator import (
    InputSchema,
    InputSchemaSample,
    OutputSchemaSample,
    PredictionType,
)
from core.tools import generate_file_id, get_chunks_from_iterable

Video = Union[str, np.ndarray]
Sample = Union[Video, Iterable[Video]]


class VideoComparatorClient(OnlinePredictionModelClient):
    VIDEOS_TO_COMPARE_BASE_BUCKET_NAME = "vc-videos-to-compare"
    MAX_BATCH_SIZE = 1

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.storage_client = StorageClient(
            key_path=self.key_path, project_id=self.project_id
        )

    @property
    def videos_to_compare_bucket(self) -> str:
        return f"{self.VIDEOS_TO_COMPARE_BASE_BUCKET_NAME}-{self.project_id}"

    def _upload_video_to_storage(self, video_path: str) -> GSPath:
        bucket = self.storage_client.client.bucket(self.videos_to_compare_bucket)

        if not bucket.exists():
            bucket.create()

        video_blob_name = generate_file_id(file_path=video_path)

        self.storage_client.upload_blob(
            source_file_name=video_path,
            bucket_name=bucket.name,
            blob_name=video_blob_name,
        )

        return GSPath.from_bucket_and_blob_names(
            bucket_name=bucket.name, blob_name=video_blob_name
        )

    def _preprocess_batch_sample_video(self, batch_sample_video: Video):
        if isinstance(batch_sample_video, str):
            return self._upload_video_to_storage(batch_sample_video)
        if isinstance(batch_sample_video, np.ndarray):
            return batch_sample_video
        raise ValueError

    def _preprocess_batch_sample(self, batch_sample: Sample) -> InputSchemaSample:
        if isinstance(batch_sample, (np.ndarray, str)):
            return InputSchemaSample(
                video=self._preprocess_batch_sample_video(batch_sample),
                other_video=None,
                prediction_type=PredictionType.VIDEO_FEATURES,
            )
        if not isinstance(batch_sample, Iterable):
            raise ValueError
        if not len(batch_sample) == 2:
            raise ValueError
        video, other_video = tuple(batch_sample)
        return InputSchemaSample(
            video=self._preprocess_batch_sample_video(video),
            other_video=self._preprocess_batch_sample_video(other_video),
            prediction_type=PredictionType.SIMILARITY,
        )

    def preprocess_batch(self, batch: Iterable[Sample]) -> InputSchema:
        return InputSchema(
            samples=[self._preprocess_batch_sample(sample) for sample in batch]
        )

    # pylint: disable=arguments-renamed
    def predict_batch(
        self,
        batch: List[Sample],
    ) -> List[np.ndarray]:
        """
        video_path_pairs: List of pairs of videos paths
        """
        input_schema = self.preprocess_batch(batch)
        endpoint = self._try_get_endpoint()
        endpoint_predictions = []
        for input_schema_samples_chunk in get_chunks_from_iterable(
            input_schema.samples, chunk_size=self.MAX_BATCH_SIZE
        ):
            endpoint_predictions += endpoint.predict(
                InputSchema(samples=input_schema_samples_chunk).to_serialized_dict()[
                    "samples"
                ]
            ).predictions
        return [
            OutputSchemaSample.parse_obj(endpoint_prediction).results
            for endpoint_prediction in endpoint_predictions
        ]
