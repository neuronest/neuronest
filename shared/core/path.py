from __future__ import annotations

import os
import re
from abc import ABC
from typing import List, Optional, Tuple
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


class GSPath(Path):
    PREFIX = "gs://"

    @classmethod
    def from_bucket_and_blob_names(
        cls, bucket_name: str, blob_name: str = ""
    ) -> GSPath:
        return cls(os.path.join(cls.PREFIX, bucket_name, blob_name))

    def to_bucket_and_blob_names(self) -> Tuple[str, str]:
        parsed_url = parse.urlparse(self)
        blob = parsed_url.path

        if blob.startswith("/"):
            blob = blob[1:]

        return parsed_url.netloc, blob

    @property
    def bucket(self) -> str:
        bucket, _ = self.to_bucket_and_blob_names()
        return bucket

    @property
    def blob_name(self) -> str:
        _, blob_name = self.to_bucket_and_blob_names()
        return blob_name


class HTTPPath(Path):
    PREFIX = "https://storage.googleapis.com/"

    def to_gs_path(self) -> GSPath:
        return GSPath(self.replace("https://storage.googleapis.com/", "gs://"))

    def to_bucket_and_blob_names(self) -> Tuple[str, str]:
        return self.to_gs_path().to_bucket_and_blob_names()

    @property
    def bucket(self) -> str:
        return self.to_gs_path().bucket

    @property
    def blob_name(self) -> str:
        return self.to_gs_path().blob_name


class LocalPath(Path):
    REGEX = r"^(?:/?[^/ ]+)+/?$"


def build_path(path: str) -> Path:
    for path_type in (GSPath, HTTPPath, LocalPath):
        if path_type.is_valid(path):
            return path_type(path)

    raise ValueError(f"Incorrect path: {path}")


def build_paths(paths: List[str]) -> List[Path]:
    return [build_path(path) for path in paths]
