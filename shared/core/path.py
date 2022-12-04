from __future__ import annotations

import os
import re
from abc import ABC
from typing import Optional, Tuple
from urllib import parse


class Path(str, ABC):
    PREFIX: Optional[str] = None
    REGEX: Optional[str] = None

    @classmethod
    def has_valid_prefix(cls, path: str) -> bool:
        if cls.PREFIX is None:
            return True

        if path.startswith(cls.PREFIX):
            return True

        return False

    @classmethod
    def has_valid_regex(cls, path: str) -> bool:
        if cls.REGEX is None:
            return True

        if bool(re.fullmatch(cls.REGEX, path)):
            return True

        return False

    @classmethod
    def is_valid(cls, path: str) -> bool:
        return cls.has_valid_prefix(path) and cls.has_valid_regex(path)

    def __new__(cls, path, *args, **kwargs):
        if not cls.has_valid_prefix(path):
            raise ValueError(
                f"Incorrect path, {cls} object does not start with "
                f"the allowed prefix: {cls.PREFIX}"
            )

        if not cls.has_valid_regex(path):
            raise ValueError(f"Incorrect local path: {path}")

        return str.__new__(cls, path, *args, **kwargs)

    @classmethod
    def from_bucket_and_blob_names(cls, bucket_name: str, blob_name: str = "") -> Path:
        return cls(os.path.join(cls.PREFIX, bucket_name, blob_name))


class GSPath(Path):
    PREFIX = "gs://"

    def to_bucket_and_blob_names(self) -> Tuple[str, str]:
        parsed_url = parse.urlparse(self)
        blob = parsed_url.path

        if blob.startswith("/"):
            blob = blob[1:]

        return parsed_url.netloc, blob


class HTTPPath(Path):
    PREFIX = "https://storage.googleapis.com/"

    def to_gs_path(self) -> GSPath:
        return GSPath(self.replace("https://storage.googleapis.com/", "gs://"))

    def to_bucket_and_blob_names(self) -> Tuple[str, str]:
        return self.to_gs_path().to_bucket_and_blob_names()


class LocalPath(Path):
    REGEX = r"^(/[^/ ]*)+/?$"


def build_path(path: str) -> Path:
    for path_type in (GSPath, HTTPPath, LocalPath):
        if path_type.is_valid(path):
            return path_type(path)

    raise ValueError(f"Incorrect path: {path}")
