import functools
import time
from typing import Any, Callable, Tuple, Union


def timeit(func: Callable[[Any], Any]) -> Callable[[Any], Union[float, Any]]:
    @functools.wraps(func)
    def timeit_wrapper(*args, **kwargs) -> Tuple[float, Any]:
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        total_time = end_time - start_time

        return total_time, result

    return timeit_wrapper


def underscore_to_hyphen(string: str):
    return string.replace("_", "-")


def hyphen_to_underscore(string: str):
    return string.replace("-", "_")
