import time
from collections import defaultdict
from typing import Any, Dict, List, Tuple

DURATIONS_KEY = "call_durations"


class TimingMeta(type):
    def __new__(cls, name: str, bases: Tuple[type, ...], attributes: Dict[str, Any]):
        for key, value in attributes.items():
            if callable(value):
                attributes[key] = cls.timer_wrapper(value)

        return super().__new__(cls, name, bases, attributes)

    @staticmethod
    def timer_wrapper(func):
        def wrapped(self, *args, **kwargs):
            start_time = time.time()
            result = func(self, *args, **kwargs)
            duration = time.time() - start_time

            durations: Dict[str, List[float]] = getattr(
                self, DURATIONS_KEY, defaultdict(list)
            )
            durations[func.__name__].append(duration)
            setattr(self, DURATIONS_KEY, durations)

            return result

        return wrapped
