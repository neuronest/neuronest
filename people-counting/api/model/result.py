from typing import List, Optional

from pydantic import BaseModel

from people_counting.common import Direction, Statistics


class Detection(BaseModel):
    timestamp: float
    direction: Direction


class PeopleCounting(BaseModel):
    detections: List[Detection]

    @classmethod
    def from_counting_statistics(cls, counting_statistics: Statistics):
        return cls(
            detections=[
                Detection(timestamp=timestamp, direction=direction)
                for timestamp, direction in zip(
                    counting_statistics.timestamps,
                    counting_statistics.passed_people_directions,
                )
            ]
        )


class JobResult(PeopleCounting):
    counted_video_storage_path: Optional[str] = None
