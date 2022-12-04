import base64
from io import BytesIO

import numpy as np


def array_to_binary(array: np.ndarray) -> bytes:
    bytes_io = BytesIO()
    # noinspection PyTypeChecker
    np.save(bytes_io, array)
    bytes_io.seek(0)

    return bytes_io.read()


def array_to_string(array: np.ndarray, encoding: str = "utf-8") -> str:
    return base64.b64encode(array_to_binary(array=array)).decode(encoding)


def array_from_binary(binary_array: bytes, allow_pickle: bool = True) -> np.ndarray:
    bytes_io = BytesIO(binary_array)

    # noinspection PyTypeChecker
    return np.load(bytes_io, allow_pickle=allow_pickle)


def array_from_string(
    encoded_array: str, encoding: str = "utf-8", allow_pickle: bool = True
) -> np.ndarray:
    return array_from_binary(
        binary_array=base64.b64decode(encoded_array.encode(encoding)),
        allow_pickle=allow_pickle,
    )
