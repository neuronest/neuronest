import os
from typing import Iterator, Optional, Tuple

import cv2 as cv
import numpy as np
from imutils import resize

from people_counting.common import BoundingBox, Statistics, Status


def read_video_as_frames(
    video_path: str,
    resized_width: Optional[int] = None,
    fps: Optional[float] = None,
    to_rgb: bool = True,
) -> Iterator[Tuple[float, np.ndarray]]:
    """
    Read a video locally, encode each frame as binary if specified.

    :param video_path: The path of the video to be read.
    :param resized_width: The desired width for each frame.
    :param fps: The desired fps, which is equal to the sampled frame rate.
    :param to_rgb: Convert each frame from BGR to RGB.

    :return: Yields a tuple containing the timestamp and one frame as a NumPy array.
    """
    if not os.path.exists(video_path):
        raise ValueError(f"The following video path is not existing: {video_path}")

    video_capture = cv.VideoCapture(video_path)

    if not video_capture.isOpened():
        raise ValueError(f"Could not open the following video: {video_path}")

    native_fps = video_capture.get(cv.CAP_PROP_FPS)
    frame_count = int(video_capture.get(cv.CAP_PROP_FRAME_COUNT))

    if fps is None:
        fps = native_fps

    duration = frame_count / fps
    sampled_frames_offsets = [
        int(time_offset * fps) for time_offset in np.arange(0, duration, 1 / fps)
    ]

    frame_number, sampled_frames_index = 0, 0
    while video_capture.isOpened():
        is_read, frame = video_capture.read()

        if not is_read:
            break

        if to_rgb:
            frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)

        while (
            sampled_frames_index < len(sampled_frames_offsets)
            and frame_number == sampled_frames_offsets[sampled_frames_index]
        ):
            time_offset = sampled_frames_index / fps

            if resized_width is None:
                yield time_offset, frame
            else:
                yield time_offset, resize(frame, width=resized_width)

            sampled_frames_index += 1

        frame_number += 1

    video_capture.release()


# pylint: disable=too-many-instance-attributes
class VideoRenderer:
    def __init__(
        self,
        line_placement_ratio: float,
        output_path: Optional[str] = None,
        enable_video_writing: bool = True,
        enable_video_showing: bool = False,
        windows_name: str = "window",
        codec: str = "mp4v",
        fps: float = 30,
    ):
        self.line_placement_ratio = line_placement_ratio
        self.output_path = output_path
        self.enable_video_writing = enable_video_writing
        self.enable_video_showing = enable_video_showing
        self.windows_name = windows_name
        self.codec = codec
        self.fps = fps
        self.writer = None

        if self.output_path is None and enable_video_writing:
            raise ValueError(
                "Unspecified output path while the video writing is enabled"
            )

        if self.output_path is not None:
            os.makedirs(os.path.dirname(self.output_path), exist_ok=True)

    def _initialize_writer(self, width: int, height: int) -> cv.VideoWriter:
        fourcc = cv.VideoWriter_fourcc(*self.codec)
        return cv.VideoWriter(self.output_path, fourcc, self.fps, (width, height), True)

    def draw_border_line(
        self,
        frame: np.ndarray,
        color: Tuple[int, int, int] = (0, 0, 0),
        width: int = 3,
    ) -> np.ndarray:
        frame_copy = frame.copy()
        horizontal_line = int(self.line_placement_ratio * frame_copy.shape[0])
        cv.line(
            frame_copy,
            (0, horizontal_line),
            (frame_copy.shape[1], horizontal_line),
            color,
            width,
        )
        return frame_copy

    @staticmethod
    def draw_bounding_box(
        frame: np.ndarray,
        bounding_box: BoundingBox,
        color: Tuple[int, int, int] = (255, 255, 255),
        width: int = 2,
    ) -> np.ndarray:
        frame_copy = frame.copy()
        cv.rectangle(
            frame_copy,
            (bounding_box.x_min, bounding_box.y_min),
            (bounding_box.x_max, bounding_box.y_max),
            color,
            width,
        )
        return frame_copy

    @staticmethod
    def draw_text(
        frame: np.ndarray,
        text: str,
        bottom_left_position: Tuple[int, int],
        font: int = cv.FONT_HERSHEY_SIMPLEX,
        font_scale: float = 0.6,
        color: Tuple[int, int, int] = (255, 255, 255),
        width: int = 2,
    ) -> np.ndarray:
        frame_copy = frame.copy()
        cv.putText(
            frame_copy,
            text,
            bottom_left_position,
            font,
            font_scale,
            color,
            width,
        )
        return frame_copy

    @staticmethod
    def draw_circle(
        frame: np.ndarray,
        center: Tuple[int, int],
        radius: int = 4,
        color: Tuple[int, int, int] = (255, 255, 255),
        thickness: int = -1,
    ) -> np.ndarray:
        frame_copy = frame.copy()
        cv.circle(
            frame_copy,
            center,
            radius,
            color,
            thickness,
        )
        return frame_copy

    @classmethod
    def draw_statistics(
        cls,
        frame: np.ndarray,
        statistics: Statistics,
        status: Status,
        frame_number: int,
    ) -> np.ndarray:
        frame_copy = frame.copy()
        stats = [
            ("Has gone up", statistics.went_up_count),
            ("Has gone down", statistics.went_down_count),
            ("Status", status),
            ("Frame", frame_number),
        ]

        for (i, (stat_name, stat_value)) in enumerate(stats):
            frame_copy = cls.draw_text(
                frame_copy,
                f"{stat_name}: {stat_value}",
                (10, frame_copy.shape[0] - ((i * 20) + 20)),
            )

        return frame_copy

    def render(self, frame: np.ndarray, to_bgr: bool = True) -> np.ndarray:
        frame_with_border = self.draw_border_line(frame)
        if to_bgr:
            frame_with_border = cv.cvtColor(frame_with_border, cv.COLOR_RGB2BGR)

        if self.enable_video_writing:
            if self.writer is None:
                height, width = frame_with_border.shape[:2]
                self.writer = self._initialize_writer(width=width, height=height)

            self.writer.write(frame_with_border)

        if self.enable_video_showing:
            cv.imshow(self.windows_name, frame_with_border)
            cv.waitKey(1) & 0xFF  # pylint: disable=expression-not-assigned

        return frame_with_border
