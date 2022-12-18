from typing import List

import numpy as np
import pytest
from core.serialization.array import (
    array_from_binary,
    array_from_string,
    array_to_binary,
    array_to_string,
)


@pytest.fixture(name="arrays")
def fixture_arrays() -> List[np.ndarray]:
    fixed_types = (int, float, str)
    fixed_shapes = ((), (1,), (10,), (5, 5), (1, 10, 5))

    return [
        np.ones(fixed_shape).astype(fixed_type)
        for fixed_shape in fixed_shapes
        for fixed_type in fixed_types
    ]


def test_array_binary(arrays: List[np.ndarray]):
    for array in arrays:
        assert np.array_equal(array_from_binary(array_to_binary(array)), array)


def test_array_string(arrays: List[np.ndarray]):
    for array in arrays:
        assert np.array_equal(array_from_string(array_to_string(array)), array)
