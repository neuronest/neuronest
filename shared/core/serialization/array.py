from io import BytesIO

import numpy as np

from core.serialization.bytes import bytes_to_string, string_to_bytes


def array_to_binary(array: np.ndarray) -> bytes:
    bytes_io = BytesIO()
    # noinspection PyTypeChecker
    np.save(bytes_io, array)
    bytes_io.seek(0)

    return bytes_io.read()


def array_to_string(array: np.ndarray, encoding: str = "utf-8") -> str:
    return bytes_to_string(array_to_binary(array=array), encoding=encoding)


def array_from_binary(binary_array: bytes, allow_pickle: bool = True) -> np.ndarray:
    bytes_io = BytesIO(binary_array)

    # noinspection PyTypeChecker
    return np.load(bytes_io, allow_pickle=allow_pickle)


def array_from_string(
    encoded_array: str, encoding: str = "utf-8", allow_pickle: bool = True
) -> np.ndarray:
    return array_from_binary(
        binary_array=string_to_bytes(encoded_array, encoding=encoding),
        allow_pickle=allow_pickle,
    )
