from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, List, Tuple


class MetricName(str, Enum):
    ABSOLUTE_ERROR_METRIC = "absolute_error_metric"


class Metric(ABC):
    @classmethod
    @abstractmethod
    def run(cls, predictions: List[Any], ground_truths: List[Any]) -> List[float]:
        pass


class AbsoluteErrorMetric(Metric):
    name: MetricName = MetricName.ABSOLUTE_ERROR_METRIC

    @classmethod
    def run(
        cls,
        predictions: List[Tuple[float, ...]],
        ground_truths: List[Tuple[float, ...]],
    ) -> List[float]:
        if len(predictions) != len(ground_truths) or any(
            len(sample_predictions) != len(sample_ground_truths)
            for sample_predictions, sample_ground_truths in zip(
                predictions, ground_truths
            )
        ):
            raise ValueError("predictions and ground truths lengths are inconsistent")

        return [
            sum(
                abs(prediction - ground_truth)
                for prediction, ground_truth in zip(
                    sample_predictions, sample_ground_truths
                )
            )
            for sample_predictions, sample_ground_truths in zip(
                predictions, ground_truths
            )
        ]
