from __future__ import annotations

from typing import Optional

from core.path import GSPath
from core.schemas.bigquery.base import BigQueryModel
from core.schemas.image_name import ImageNameWithTag


class TrainingMetrics(BigQueryModel):
    __bigquery_tablename__ = "training_metrics"
    model_name: str
    training_duration: float
    metrics: dict
    parameters: dict
    model_path: GSPath
    image_name: ImageNameWithTag
    global_metric_name: Optional[str] = None
    global_metric: Optional[float] = None


class ScoringJob(BigQueryModel):
    __bigquery_tablename__ = "scoring_job"
    service_name: str
    scoring_id: str
    dataset_id: str


class ScoringDataset(BigQueryModel):
    __bigquery_tablename__ = "scoring_dataset"
    path: str
    name: str
    md5: str
    size: int
    nfiles: int


class ScoringAsset(BigQueryModel):
    __bigquery_tablename__ = "scoring_asset"
    scoring_id: str
    path: str
    score: float
