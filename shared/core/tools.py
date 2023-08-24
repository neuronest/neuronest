import hashlib
import os
from functools import wraps
from typing import Any, Callable, Iterable, Iterator, List, Optional


def get_chunks_from_iterable(
    iterable: Iterable[Any], chunk_size: int, step: Optional[int] = None
) -> Iterator[List[Any]]:
    """
    Parse and split an iterable into chunks.

    :param iterable: The iterable to be parsed.
    :param chunk_size: The size of each chunk to be yielded.
    The last chunk may have a smaller size.
    :param step: Optional, define the intersection between two chunks.
    If not specified, it will be set to chunk_size: there will be no intersection
    between two consecutive chunks.
    If set to 1, two consecutive chunks will have the same content, except one element
    (the first for the first chunk, the last for the second chunk).
    """
    chunk_size = max(chunk_size, 1)
    if step is None:
        step = chunk_size
    else:
        step = min(max(step, 1), chunk_size)

    chunk = []
    still_remaining = False
    for element in iterable:
        chunk.append(element)
        still_remaining = True

        if len(chunk) == chunk_size:
            yield chunk
            chunk = chunk[step:]
            still_remaining = False

    if len(chunk) > 0 and still_remaining is True:
        yield chunk


def extract_file_extension(path: str) -> str:
    extension = os.path.splitext(path)[-1]

    if extension == "":
        raise ValueError(f"Unable to get the file extension from '{path}'")

    return extension


def maybe_async(convert_to_async: bool) -> Callable:
    """
    Make a sync or async function dynamically.
    Useful in some cases for debug where the
    function must then be def or async def for example
    """

    def decorator(func):
        if convert_to_async is True:

            @wraps(func)
            async def async_func(*args, **kwargs):
                return await func(*args, **kwargs)

            return async_func

        return func

    return decorator


def get_file_id_from_path(
    file_path: str,
    add_filename: bool = True,
    add_extension: bool = True,
):
    file_path_without_extension, extension = os.path.splitext(file_path)
    with open(file_path, "rb") as file_reader:
        file_hash_hexdigest = hashlib.sha256(file_reader.read()).hexdigest()

    if add_filename:
        file_id = (
            f"{os.path.basename(file_path_without_extension)}_{file_hash_hexdigest}"
        )
    else:
        file_id = file_hash_hexdigest
    if add_extension and extension:
        file_id += extension
    return file_id
