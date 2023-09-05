import os
from typing import Optional, Tuple

import cv2 as cv
import numpy as np
from core.schemas.asset import rgb_to_bgr

from people_counting.common import BoundingBox, Statistics, Status


class VideoRenderer:
    def __init__(
        self,
        line_placement_ratio: float,
        fps: float,
        output_path: Optional[str] = None,
        enable_video_writing: bool = False,
        enable_video_showing: bool = False,
    ):
        self.line_placement_ratio = line_placement_ratio
        self.fps = fps
        self.output_path = output_path
        self.enable_video_writing = enable_video_writing
        self.enable_video_showing = enable_video_showing

        # will be initialized once a frame is processed
        self.writer: Optional[cv.VideoWriter] = None

        if self.output_path is None and enable_video_writing:
            raise ValueError(
                "Unspecified output path while the video writing is enabled"
            )

        if self.output_path is not None:
            os.makedirs(os.path.dirname(self.output_path), exist_ok=True)

    def _initialize_writer(
        self, width: int, height: int, codec: str = "h264"
    ) -> cv.VideoWriter:
        fourcc = cv.VideoWriter_fourcc(*codec)

        return cv.VideoWriter(self.output_path, fourcc, self.fps, (width, height), True)

    def _draw_border_line(
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
    def _draw_text(
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
    def _draw_circle(
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

    @classmethod
    def draw_bounding_box_id(
        cls,
        frame: np.ndarray,
        object_id: int,
        centroid_x: int,
        centroid_y: int,
        margin: int = 10,
    ) -> np.ndarray:
        frame_copy = frame.copy()

        drawn_frame = cls._draw_text(
            frame=frame_copy,
            text=f"ID {object_id}",
            bottom_left_position=(centroid_x - margin, centroid_y - margin),
        )
        drawn_frame = cls._draw_circle(
            frame=drawn_frame, center=(centroid_x, centroid_y)
        )

        return drawn_frame

    def draw_statistics_on_frame(
        self,
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

        frame_copy = self._draw_border_line(frame_copy)

        for (i, (stat_name, stat_value)) in enumerate(stats):
            frame_copy = self._draw_text(
                frame_copy,
                f"{stat_name}: {stat_value}",
                (10, frame_copy.shape[0] - ((i * 20) + 20)),
            )

        return frame_copy

    def render(
        self, frame: np.ndarray, to_bgr: bool = True, windows_name: str = "window"
    ) -> np.ndarray:
        frame_copy = frame.copy()

        if to_bgr:
            frame_copy = rgb_to_bgr(frame_copy)

        if self.enable_video_writing:
            if self.writer is None:
                height, width = frame_copy.shape[:2]
                self.writer = self._initialize_writer(width=width, height=height)

            self.writer.write(frame_copy)

        if self.enable_video_showing:
            cv.imshow(windows_name, frame_copy)
            cv.waitKey(1000 * 100) & 0xFF  # pylint: disable=expression-not-assigned

        return frame_copy
