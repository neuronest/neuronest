from __future__ import annotations

import re
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, List, Tuple

from pydantic import BaseModel

from core.schemas.image_name import ImageNameWithTag


class EvaluatedServiceName(str, Enum):
    PEOPLE_COUNTING = "people_counting"


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


class DatasetName(str):
    SUFFIX: str = "_dataset"
    REGEX: str = rf"^([a-z_]+){SUFFIX}$"

    @classmethod
    def from_service_name(cls, service_name: str) -> DatasetName:
        return cls(service_name + cls.SUFFIX)

    @classmethod
    def is_valid(cls, dataset_name: str) -> bool:
        matches = re.fullmatch(cls.REGEX, dataset_name)

        if matches is None:
            return False

        return matches.group(1) in list(EvaluatedServiceName)

    def __new__(cls, dataset_name, *args, **kwargs):
        if not cls.is_valid(dataset_name):
            raise ValueError(f"Incorrect dataset name: {dataset_name}")

        return str.__new__(cls, dataset_name, *args, **kwargs)

    def to_service_name(self) -> EvaluatedServiceName:
        return EvaluatedServiceName(re.fullmatch(self.REGEX, self).groups(1))


class ResourcesOutput(BaseModel):
    resource: str


class EvaluateJobDocument(BaseModel):
    job_id: str
    job_date: datetime
    service_name: EvaluatedServiceName
    image_name: ImageNameWithTag


class EvaluateResultsDocument(BaseModel):
    job_id: str
    dataset_id: str
    job_date: datetime
    service_name: EvaluatedServiceName
    service_image_name: ImageNameWithTag
    metric_name: MetricName
    scoring_ids: List[str]
    paths: List[str]
    scores: List[float]


class ServiceEvaluatorInput(BaseModel):
    reuse_already_computed_results: bool = True


class ServiceEvaluatorOutput(BaseModel):
    job_id: str
