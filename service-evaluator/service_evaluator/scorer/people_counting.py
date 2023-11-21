from typing import List

import pandas as pd
from core.schemas.people_counting import Direction, PeopleCounterAssetResultsDocument
from core.schemas.service_evaluator import EvaluatedServiceName

from service_evaluator.dataset_manager import DatasetManager
from service_evaluator.scorer.base import ScorableDocument, ScorerMixin


class PeopleCountingScorableDocument(ScorableDocument):
    people_in: int
    people_out: int


class PeopleCountingScorer(ScorerMixin):
    service_name: EvaluatedServiceName = EvaluatedServiceName.PEOPLE_COUNTING

    def convert_dataset_to_scorable_documents(
        self, dataset: pd.DataFrame
    ) -> List[PeopleCountingScorableDocument]:
        return [
            PeopleCountingScorableDocument(people_in=people_in, people_out=people_out)
            for people_in, people_out in zip(dataset.people_in, dataset.people_out)
        ]

    def convert_predictions_to_scorable_documents(
        self, predictions: List[PeopleCounterAssetResultsDocument]
    ) -> List[PeopleCountingScorableDocument]:
        return [
            PeopleCountingScorableDocument(
                people_in=len(
                    [
                        detection
                        for detection in prediction.detections
                        if detection.direction == Direction.DOWN
                    ]
                ),
                people_out=len(
                    [
                        detection
                        for detection in prediction.detections
                        if detection.direction == Direction.UP
                    ]
                ),
            )
            for prediction in predictions
        ]

    def run(
        self,
        dataset_manager: DatasetManager,
        predictions: List[PeopleCounterAssetResultsDocument],
    ) -> List[float]:
        real_documents = self.convert_dataset_to_scorable_documents(
            dataset=dataset_manager.dataset
        )
        prediction_documents = self.convert_predictions_to_scorable_documents(
            predictions=predictions
        )

        if len(real_documents) != len(prediction_documents):
            raise ValueError(
                "Lengths are mismatching between real_documents and"
                "prediction_documents"
            )

        return [
            abs(real_document.people_in - prediction_document.people_in)
            + abs(real_document.people_out - prediction_document.people_out)
            for real_document, prediction_document in zip(
                real_documents, prediction_documents
            )
        ]
