from typing import List

from core.schemas.people_counting import Detection, Direction


def are_detections_correct(
    detections: List[Detection], up_amount: int, down_amount: int
) -> bool:
    return up_amount == sum(
        detection.direction == Direction.UP for detection in detections
    ) and down_amount == sum(
        detection.direction == Direction.DOWN for detection in detections
    )
