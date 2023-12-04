import hashlib
import os
from typing import Any, Iterable, Iterator, List, Optional, Tuple


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


def merge_chunks_get_elements(chunks: Iterable[Iterable[Any]]) -> Any:
    for chunk in chunks:
        for element in chunk:
            yield element


def split_list_into_two_parts(elements: List[Any]) -> Tuple[List[Any], List[Any]]:
    if len(elements) <= 1:
        return elements, []

    middle_index = len(elements) // 2

    return elements[:middle_index], elements[middle_index:]


def extract_file_extension(path: str) -> str:
    extension = os.path.splitext(path)[-1]

    if extension == "":
        raise ValueError(f"Unable to get the file extension from '{path}'")

    return extension


def generate_file_id(
    file_path: str,
    include_name: bool = False,
    include_extension: bool = True,
) -> str:
    """
    Generate a unique ID based on the sha256 hash of the file content.
    Optionally include the original filename and extension.

    :param file_path: str, path to the file
    :param include_name: bool, flag to include original filename in the ID
    :param include_extension: bool, flag to include file extension in the ID
    :return: str, generated file ID
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"The file at path {file_path} does not exist.")

    file_path_without_extension, extension = os.path.splitext(file_path)

    with open(file_path, "rb") as file_reader:
        file_id = hashlib.sha256(file_reader.read()).hexdigest()

    if include_name is True:
        file_id = f"{os.path.basename(file_path_without_extension)}_{file_id}"
    if include_extension is True and extension != "":
        file_id += extension

    return file_id
