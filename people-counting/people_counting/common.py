import logging
from dataclasses import dataclass
from enum import Enum
from functools import wraps
from time import time
from typing import Callable, Tuple

import pandas as pd

from shared.core.schemas.people_counting import Direction

VIDEOS_EXTENSIONS = [".avi", ".mp4"]


def init_logger(level: int):
    default_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=level, format=default_format)


def timed(
    func: Callable,
    runtime_timing_key: str = "run_duration",
):
    """
    Encapsulate a callable object with a timing function.

    It can be used as method decorator to monitor timing executions.

    :param func: any function to wrap
    :param runtime_timing_key: class attribute which will contain timings for every
    wrapped methods.

    :return: The wrapped function.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        self = next(iter(args))
        if hasattr(self, runtime_timing_key):
            runtime = getattr(self, runtime_timing_key)
        else:
            runtime = {}
            self.runtime = runtime
        start = time()
        result = func(*args, **kwargs)
        end = time()
        runtime[func.__name__] = round(end - start, 2)
        return result

    return wrapper


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
