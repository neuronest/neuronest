import hashlib
from typing import List


def combine_hashes(hashes: List[str]) -> str:
    return hashlib.md5("".join(sorted(hashes)).encode()).hexdigest()
