from typing import Dict, List

from core.client.people_counting import PeopleCountingClient
from core.schemas.people_counting import PeopleCounterAssetResultsDocument
from core.schemas.service_evaluator import EvaluatedServiceName

from service_evaluator.dataset_manager import DatasetManager
from service_evaluator.predictor.base import PredictorMixin


class PeopleCountingPredictor(PredictorMixin):
    service_name: EvaluatedServiceName = EvaluatedServiceName.PEOPLE_COUNTING

    def __init__(self, service_client_parameters: Dict[str, str]):
        super().__init__(
            service_client_parameters=service_client_parameters,
            service_name=self.service_name,
            expected_client_class=PeopleCountingClient,
        )

    def run(
        self, dataset_manager: DatasetManager
    ) -> List[PeopleCounterAssetResultsDocument]:
        return self.client.count_people_sync(
            videos_paths=dataset_manager.asset_paths,
            save_counted_videos_in_storage=False,
        )
