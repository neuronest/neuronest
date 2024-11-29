from core.client.model_client.abstract.online_prediction_model import (
    OnlinePredictionModelClient,
)
from core.schemas.modules.video_comparator import InputSampleSchema, OutputSampleSchema


class VideoComparatorModelClient(OnlinePredictionModelClient):
    INPUT_SAMPLE_SCHEMA = InputSampleSchema
    OUTPUT_SAMPLE_SCHEMA = OutputSampleSchema
