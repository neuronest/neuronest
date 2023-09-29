import os
from typing import Any, Iterable, Iterator, List, Optional


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
