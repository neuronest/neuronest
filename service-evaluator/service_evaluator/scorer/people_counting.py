from __future__ import annotations

from typing import List, Type

import pandas as pd
from core.schemas.people_counting import Direction, PeopleCounterAssetResultsDocument
from core.schemas.service_evaluator import EvaluatedServiceName

from service_evaluator.scorer.base import ScorableDocument, ScorerMixin
from service_evaluator.scorer.metrics import AbsoluteErrorMetric, Metric


class PeopleCountingScorableDocument(ScorableDocument):
    people_in: int
    people_out: int


class PeopleCountingScorer(ScorerMixin):
    service_name: EvaluatedServiceName = EvaluatedServiceName.PEOPLE_COUNTING
    scorable_document_class: Type[ScorableDocument] = PeopleCountingScorableDocument
    metric: Type[Metric] = AbsoluteErrorMetric

    def convert_dataset_to_scorable_documents(
        self, dataset: pd.DataFrame
    ) -> List[PeopleCountingScorer.scorable_document_class]:
        return [
            self.scorable_document_class(people_in=people_in, people_out=people_out)
            for people_in, people_out in zip(dataset.people_in, dataset.people_out)
        ]

    def convert_predictions_to_scorable_documents(
        self, predictions: List[PeopleCounterAssetResultsDocument]
    ) -> List[PeopleCountingScorer.scorable_document_class]:
        return [
            self.scorable_document_class(
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
        real_documents: List[PeopleCountingScorer.scorable_document_class],
        prediction_documents: List[PeopleCountingScorer.scorable_document_class],
    ) -> List[float]:
        if len(real_documents) != len(prediction_documents):
            raise ValueError(
                "Lengths are mismatching between real_documents and"
                "prediction_documents"
            )

        return self.metric.run(
            predictions=[
                (prediction_document.people_in, prediction_document.people_out)
                for prediction_document in prediction_documents
            ],
            ground_truths=[
                (real_document.people_in, real_document.people_out)
                for real_document in real_documents
            ],
        )
