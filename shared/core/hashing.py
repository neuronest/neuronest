import hashlib
from typing import Iterable


def combine_hashes(hashes: Iterable[str], reorder: bool = True) -> str:
    if reorder is True:
        hashes = sorted(hashes)

    return hashlib.md5("".join(hashes).encode()).hexdigest()
