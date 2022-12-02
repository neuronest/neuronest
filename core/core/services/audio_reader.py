import contextlib
import json
import logging
import subprocess
import tempfile
from shlex import quote
from typing import Dict, List, Optional

import ffmpeg
from ffmpeg import Error as FfmpegError
from pydantic import BaseModel, validator

from neuronest.core.google.storage_client import StorageClient
from neuronest.core.path import LocalPath, build_path
from neuronest.core.schemas.asset import (
    AUDIO_CODEC_TO_CONTAINER,
    AssetType,
    AudioContent,
    AudioExtension,
)
from neuronest.core.services.reader_common import (
    infer_asset_type,
    retrieve_asset_locally,
)

logger = logging.getLogger(__name__)


class AudioStream(BaseModel):
    codec_type: str
    codec_name: str = "default_codec_name"  # may not be present


class AudioMetadata(BaseModel):
    streams: List[AudioStream]
    # custom fields
    audio_codec_to_container: Dict[str, AudioExtension]

    @validator("streams")
    # pylint: disable=no-self-argument
    def keep_audio_stream_only(cls, streams: List[AudioStream]) -> List[AudioStream]:
        return [stream for stream in streams if stream.codec_type == "audio"]

    @property
    def codec_name(self) -> Optional[AudioExtension]:
        if len(self.streams) != 1:
            if len(self.streams) > 1:
                logger.warning(
                    "The video contains more than one audio track. Unsupported."
                )
            return None

        raw_codec_name = self.streams[0].codec_name

        if raw_codec_name not in self.audio_codec_to_container:
            logger.warning(f"Unknown audio codec {raw_codec_name}.")
            return None

        return self.audio_codec_to_container[raw_codec_name]


def extract_audio_metadata(video_path: LocalPath) -> AudioMetadata:
    raw_output = subprocess.check_output(
        [
            "ffprobe",
            "-show_format",
            "-show_streams",
            "-loglevel",
            "quiet",
            "-print_format",
            "json",
            f"{quote(video_path)}",
        ]
    )

    return AudioMetadata(
        **json.loads(raw_output), audio_codec_to_container=AUDIO_CODEC_TO_CONTAINER
    )


def get_audio_container(video_path: LocalPath) -> Optional[AudioExtension]:
    """
    Allow to determine the appropriate audio container according to the audio codec
    used in the video.

    :param video_path: The path of the video.

    :return: The appropriate container if the codec is supported, else None.
    """
    return extract_audio_metadata(video_path).codec_name


@contextlib.contextmanager
def extract_encoded_audio(video_path: LocalPath) -> Optional[str]:
    """
    Generate a temporary audio file out of the video, which is the encoded audio of the
    video (i.e. without having to decode and re-encode it, which could lead to avoidable
    information loss).

    :param video_path: The path of the video

    :return: A temporary audio path if the encoded audio could have been extracted,
    else None
    """
    audio_container = get_audio_container(video_path)

    if audio_container is None:
        logger.warning(f"No audio detected in the video path: '{video_path}'.")
        yield None
        return

    with tempfile.NamedTemporaryFile(
        suffix=f".{audio_container}", delete=False
    ) as temporary_file:
        audio_path = temporary_file.name
        stream = ffmpeg.input(video_path)
        stream = stream.audio
        stream = ffmpeg.output(stream, audio_path, c="copy")

        try:
            ffmpeg.run(stream, quiet=True, overwrite_output=True)
        except FfmpegError:
            logger.error(
                f"A FFmpeg error has be encountered during the audio extraction in the "
                f"video path: '{video_path}'."
            )
            yield None
            return

        yield audio_path


def make_audio_content(
    asset_path: str,
    storage_client: Optional[StorageClient] = None,
) -> Optional[AudioContent]:
    asset_path = build_path(asset_path)

    asset_type = infer_asset_type(asset_path)
    if asset_type == AssetType.IMAGE:
        raise ValueError("Images are not supported")

    with retrieve_asset_locally(
        asset_path=asset_path, storage_client=storage_client
    ) as (_, local_asset_path):
        with extract_encoded_audio(local_asset_path) as encoded_audio_path:
            if encoded_audio_path is None:
                return None

            # delete should always be True because the encoded part is extracted in
            # a temporary file in any case
            return AudioContent(asset_path=encoded_audio_path, delete=True)
