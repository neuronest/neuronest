from abc import ABC, abstractmethod
from typing import List, TypeVar

import pandas as pd
from pydantic import BaseModel

PredictionDocument = TypeVar("PredictionDocument", bound="BaseModel")


class ScorableDocument(BaseModel):
    pass


class ScorerMixin(ABC):
    @abstractmethod
    def convert_dataset_to_scorable_documents(
        self, dataset: pd.DataFrame
    ) -> List[ScorableDocument]:
        raise NotImplementedError

    @abstractmethod
    def convert_predictions_to_scorable_documents(
        self, predictions: List[PredictionDocument]
    ) -> List[ScorableDocument]:
        raise NotImplementedError

    @abstractmethod
    def run(
        self,
        real_documents: List[ScorableDocument],
        prediction_documents: List[ScorableDocument],
    ) -> List[float]:
        raise NotImplementedError
