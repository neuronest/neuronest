import logging
from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple

import pandas as pd
from core.schemas.people_counting import Detection, Direction


def init_logger(level: int):
    default_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=level, format=default_format)


class Statistics:
    def __init__(self):
        self.passed_people_directions = []
        self.timestamps = []

    def add_went_up(self, timestamp: float):
        self.passed_people_directions.append(Direction.UP)
        self.timestamps.append(timestamp)

    def add_went_down(self, timestamp: float):
        self.passed_people_directions.append(Direction.DOWN)
        self.timestamps.append(timestamp)

    @property
    def went_up_count(self) -> int:
        return len(
            [elem for elem in self.passed_people_directions if elem == Direction.UP]
        )

    @property
    def went_down_count(self) -> int:
        return len(
            [elem for elem in self.passed_people_directions if elem == Direction.DOWN]
        )

    def to_df(self) -> pd.DataFrame:
        return pd.DataFrame(
            columns=["timestamp", "count"],
            data={
                "timestamp": self.timestamps,
                "count": self.passed_people_directions,
            },
        )

    def to_detections(self) -> List[Detection]:
        return [
            Detection(timestamp=timestamp, direction=direction)
            for timestamp, direction in zip(
                self.timestamps, self.passed_people_directions
            )
        ]


class Status(str, Enum):
    DETECTING = "detecting"
    TRACKING = "tracking"


@dataclass
class BoundingBox:
    x_min: int
    y_min: int
    x_max: int
    y_max: int

    def __post_init__(self):
        self.x_min = int(self.x_min)
        self.y_min = int(self.y_min)
        self.x_max = int(self.x_max)
        self.y_max = int(self.y_max)

    @property
    def center(self) -> Tuple[int, int]:
        return int((self.x_min + self.x_max) / 2), int((self.y_min + self.y_max) / 2.0)
