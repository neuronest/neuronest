from __future__ import annotations as type_annotations

import contextlib
import os
import tempfile
from abc import ABC
from enum import Enum
from typing import Any, Iterator, List, Optional, Union

import librosa
import numpy as np
from cv2 import cv2 as cv
from moviepy.audio.io.AudioFileClip import AudioFileClip
from pydantic import BaseModel, root_validator, validator

from neuronest.core.fixed_parameters import TIME_STEP
from neuronest.core.path import LocalPath
from neuronest.core.tools import extract_file_extension, get_chunks_from_iterable

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".mpg", ".mpeg", ".m4v", ".webm", ".avi"}


class AssetType(str, Enum):
    VIDEO = "video"
    IMAGE = "image"


class AudioCodec(str, Enum):
    AAC = "aac"
    WMAV2 = "wmav2"
    OPUS = "opus"


class AudioExtension(str, Enum):
    M4A = "m4a"
    WMA = "wma"
    OPUS = "opus"


AUDIO_CODEC_TO_CONTAINER = {
    AudioCodec.AAC: AudioExtension.M4A,
    AudioCodec.WMAV2: AudioExtension.WMA,
    AudioCodec.OPUS: AudioExtension.OPUS,
}


class AssetMeta(ABC, BaseModel):
    asset_type: AssetType
    width: int
    height: int
    # do not specify the following attributes (ratio and surface), because they can be
    # deduced from the others
    ratio: Optional[float] = None
    surface: Optional[float] = None

    @root_validator
    # pylint: disable=no-self-argument
    def populate_ratio_and_surface(cls, values: dict) -> dict:
        values["ratio"] = values["width"] / values["height"]
        values["surface"] = values["width"] * values["height"]

        return values


class ImageAssetMeta(AssetMeta):
    asset_type: AssetType = AssetType.IMAGE


class VideoAssetMeta(AssetMeta):
    asset_type: AssetType = AssetType.VIDEO
    frames_number: int
    sampled_frames_number: int
    fps: float
    time_step: float
    # do not specify the duration, because it can be deduced from the other fields
    duration: float

    @root_validator(pre=True)
    # pylint: disable=no-self-argument
    def populate_duration(cls, values: dict) -> dict:
        values["duration"] = values["frames_number"] / values["fps"]

        return values


def build_asset_meta(
    asset_meta: Union[AssetMeta, dict]
) -> Union[VideoAssetMeta, ImageAssetMeta]:
    if isinstance(asset_meta, (VideoAssetMeta, ImageAssetMeta)):
        return asset_meta

    asset_type = asset_meta["asset_type"]

    if asset_type == AssetType.VIDEO:
        return VideoAssetMeta.parse_obj(asset_meta)

    if asset_type == AssetType.IMAGE:
        return ImageAssetMeta.parse_obj(asset_meta)

    raise ValueError(f"Unknown asset type: {asset_type}")


class AssetContent(BaseModel, ABC):
    asset_path: LocalPath
    delete: bool = False

    @validator("asset_path", pre=True)
    # pylint: disable=no-self-argument
    def assert_file_exists(cls, asset_path: str) -> LocalPath:
        if not os.path.exists(asset_path):
            raise ValueError(f"The following asset path is not existing: {asset_path}")

        return LocalPath(asset_path)

    class Config:
        arbitrary_types_allowed = True

    @property
    def content(self) -> Any:
        raise NotImplementedError

    @property
    def binary_content(self) -> Union[bytes, Iterator[bytes]]:
        raise NotImplementedError

    @property
    def as_array_content(self) -> np.ndarray:
        raise NotImplementedError

    def __del__(self):
        if self.delete and os.path.exists(self.asset_path):
            os.unlink(self.asset_path)


class VisualAssetContent(AssetContent, ABC):
    asset_meta: AssetMeta

    @staticmethod
    def to_binary(frame: np.ndarray, extension: str = ".jpg") -> bytes:
        """Convert the given frame to binary"""
        return cv.imencode(extension, frame)[1].tobytes()


class ImageAssetContent(VisualAssetContent):
    asset_meta: ImageAssetMeta
    # fields filled with validators
    image: np.ndarray

    @root_validator(pre=True)
    # pylint: disable=no-self-argument
    def fill_image(cls, values: dict) -> dict:
        asset_path = values["asset_path"]
        values["image"] = cv.imread(asset_path)

        if values["image"] is None:
            raise ValueError(f"Image could not be loaded from path: {asset_path}")

        return values

    @root_validator(pre=True)
    # pylint: disable=no-self-argument
    def fill_metadata(cls, values: dict) -> dict:
        values["extension"] = os.path.splitext(values["asset_path"])[-1]

        values["asset_meta"] = ImageAssetMeta(
            width=values["image"].shape[1],
            height=values["image"].shape[0],
        )

        return values

    @property
    def content(self) -> np.ndarray:
        return self.image

    @property
    def binary_content(self) -> bytes:
        return self.to_binary(self.content)

    @property
    def as_array_content(self) -> np.ndarray:
        return self.content


class VideoAssetContent(VisualAssetContent):
    asset_meta: VideoAssetMeta
    time_step: float

    @staticmethod
    def estimate_sampled_frames_number(
        frames_number: int, initial_fps: float, targeted_time_step: float
    ) -> int:
        duration = frames_number / initial_fps

        return len(np.arange(0, duration, targeted_time_step))

    @classmethod
    @contextlib.contextmanager
    def _capture_video(cls, asset_path: str) -> cv.VideoCapture:
        """Instantiate and return a VideoCapture instance"""
        video_capture = None
        try:
            video_capture = cv.VideoCapture(asset_path)

            yield video_capture
        finally:
            video_capture.release()

    @classmethod
    def _read(cls, asset_path: str) -> Iterator[np.ndarray]:
        with cls._capture_video(asset_path) as video_capture:
            while video_capture.isOpened():
                is_read, frame = video_capture.read()
                if not is_read:
                    break
                yield frame
            else:
                raise ValueError(f"Could not open the following asset: {asset_path}")

    @root_validator(pre=True)
    # pylint: disable=no-self-argument
    def fill_time_step(cls, values: dict) -> dict:
        if values.get("time_step") is None:
            values["time_step"] = TIME_STEP

        return values

    @root_validator(pre=True)
    # pylint: disable=no-self-argument
    def fill_metadata(cls, values: dict) -> dict:
        asset_path, targeted_time_step = values["asset_path"], values["time_step"]

        with cls._capture_video(asset_path) as video_capture:
            initial_fps = int(video_capture.get(cv.CAP_PROP_FPS))
            width = int(video_capture.get(cv.CAP_PROP_FRAME_WIDTH))
            height = int(video_capture.get(cv.CAP_PROP_FRAME_HEIGHT))
            # the exact number of frames cannot be properly retrieved using
            # cv.CAP_PROP_FRAME_COUNT because it does not take into account
            # unreadable/corrupted frames, resulting in a potential small difference
            # between the cv.CAP_PROP_FRAME_COUNT value and the actual number of frames
            # read subsequently
            frames_number = sum(1 for _ in cls._read(asset_path))

        sampled_frames_number = cls.estimate_sampled_frames_number(
            frames_number=frames_number,
            initial_fps=initial_fps,
            targeted_time_step=targeted_time_step,
        )

        values["asset_meta"] = VideoAssetMeta(
            asset_type=AssetType.VIDEO,
            width=width,
            height=height,
            frames_number=frames_number,
            fps=initial_fps,
            sampled_frames_number=sampled_frames_number,
            time_step=targeted_time_step,
        )

        return values

    def _get_frames(self) -> Iterator[np.ndarray]:
        duration = self.asset_meta.frames_number / self.asset_meta.fps

        sampled_frames_offsets = tuple(
            int(time_offset * self.asset_meta.fps)
            for time_offset in np.arange(0, duration, self.time_step)
        )

        sampled_frames_index = 0
        for frame_number, frame in enumerate(self._read(self.asset_path)):
            while (
                sampled_frames_index < len(sampled_frames_offsets)
                and frame_number == sampled_frames_offsets[sampled_frames_index]
            ):
                yield frame

                sampled_frames_index += 1

    @property
    def content(self) -> Iterator[np.ndarray]:
        return self._get_frames()

    @property
    def binary_content(self) -> Iterator[bytes]:
        for frame in self._get_frames():
            yield self.to_binary(frame)

    @property
    def as_array_content(self) -> np.ndarray:
        """Convert the frames as a single 4-D (T, W, H, C) NumPy array."""
        return np.array(list(self.content))

    @property
    def frame_offsets(self) -> List[int]:
        return list(range(self.asset_meta.sampled_frames_number))

    def chunks(
        self, chunk_size: int = 10, as_binary: bool = False
    ) -> Iterator[List[Union[np.ndarray, bytes]]]:
        """Chunk the content sampled frames into chunks of the given size"""
        iterator = self.binary_content if as_binary else self.content

        return get_chunks_from_iterable(iterator, chunk_size)

    def get_frame_at_index(
        self, index: int, as_binary: bool = False
    ) -> Union[np.ndarray, bytes]:
        for current_index, frame in enumerate(self.content):
            if current_index == index:
                if as_binary:
                    return self.to_binary(frame)

                return frame

        raise IndexError(f"index={index} is out of range")

    def get_frame_at_indexes(
        self, indexes: List[int], as_binary: bool = False
    ) -> Iterator[Union[np.ndarray, bytes]]:
        if len(indexes) != len(set(indexes)):
            raise ValueError("Received indexes should be unique")

        if indexes != sorted(indexes):
            raise ValueError("Received indexes should be ordered")

        if not all(
            0 <= index < self.asset_meta.sampled_frames_number for index in indexes
        ):
            raise ValueError("Received some out of range indexes")

        for current_index, frame in enumerate(self.content):
            if current_index in indexes:
                if as_binary:
                    yield self.to_binary(frame)

                else:
                    yield frame


class AudioContent(AssetContent):
    asset_path: LocalPath
    delete: bool = False
    # fields filled with validators
    extension: str
    audio_clip: AudioFileClip
    audio_array: np.ndarray

    @staticmethod
    def audio_clip_to_array(audio_clip: AudioFileClip) -> np.ndarray:
        # audio_clip is a kind of iterator and the method to_soundarray does not seem
        # to be callable more than once without rebuild an AudioFileClip instance
        return np.expand_dims(
            librosa.to_mono(audio_clip.to_soundarray().T), axis=0
        ).astype("float32")

    @classmethod
    def from_bytes(cls, raw_audio: bytes, extension: str):
        with tempfile.NamedTemporaryFile(suffix=extension) as temporary_file:
            with open(temporary_file.name, "wb") as fp:
                fp.write(raw_audio)

            return cls(asset_path=temporary_file.name, delete=True)

    @root_validator(pre=True)
    # pylint: disable=no-self-argument
    def fill_audio_clip(cls, values: dict) -> dict:
        asset_path = values["asset_path"]

        values["extension"] = extract_file_extension(asset_path)
        values["audio_clip"] = AudioFileClip(asset_path)

        if values["audio_clip"] is None:
            raise ValueError(f"Audio could not be loaded from path: {asset_path}")

        values["audio_array"] = cls.audio_clip_to_array(values["audio_clip"])

        return values

    @property
    def content(self) -> AudioFileClip:
        return self.audio_clip

    @property
    def binary_content(self) -> bytes:
        with open(self.asset_path, "rb") as fp:
            return fp.read()

    @property
    def as_array_content(self) -> np.ndarray:
        return self.audio_array
