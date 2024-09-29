import functools
import time
from typing import Any, Callable, List, Optional, Set, Tuple, Union


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


def string_to_boolean(string: str) -> bool:
    boolean_string_true = "true"
    boolean_string_false = "false"
    if (lower_string := string.lower()) in {boolean_string_true, boolean_string_false}:
        return lower_string == boolean_string_true

    raise ValueError(f"Invalid string to interpolate: {string}")


def xor_not_none(value: Optional[Any], other_value: Optional[Any]) -> bool:
    return (value is not None) != (other_value is not None)


def contains_only_n_element(
    elements: Union[List[Any], Set[Any], Tuple[Any, ...]], n: int
) -> bool:
    return len(elements) == n


def contains_only_one_element(
    elements: Union[List[Any], Set[Any], Tuple[Any, ...]]
) -> bool:
    return contains_only_n_element(elements=elements, n=1)
