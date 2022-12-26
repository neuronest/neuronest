import logging
import os
from typing import Dict, List, Optional

import cv2 as cv
import dlib
import pandas as pd
from model.modules.model import Model
from omegaconf import DictConfig

from people_counting.centroid_tracker import CentroidTracker
from people_counting.common import BoundingBox, Statistics, Status, timed
from people_counting.config import cfg
from people_counting.trackable_object import TrackableObject
from people_counting.video_handler import VideoRenderer, read_video_as_frames

logger = logging.getLogger(__name__)


class PeopleCounter:
    def __init__(
        self,
        model_config: DictConfig,
        algorithm_config: DictConfig,
        image_width: int,
        video_outputs_directory: Optional[str] = None,
    ):
        self.image_width = image_width
        self.video_outputs_directory = video_outputs_directory
        self.algorithm_config = algorithm_config
        self.model = Model(
            model_type=model_config.model_type,
            model_name=model_config.model_name,
            confidence_threshold=model_config.confidence_threshold,
        )

        if self.video_outputs_directory is not None:
            os.makedirs(video_outputs_directory, exist_ok=True)

        self.run_duration: Dict[str, float] = {}

    def get_video_output_path(self, video_input_path: str) -> str:
        return os.path.join(
            self.video_outputs_directory, os.path.basename(video_input_path)
        )

    # pylint: disable=too-many-branches,too-many-locals
    @timed
    def run(
        self,
        video_input_path: str,
        enable_video_writing: bool = False,
        enable_video_showing: bool = False,
        video_is_rgb_color: bool = True,
    ) -> pd.DataFrame:
        video_output_path = self.get_video_output_path(video_input_path)
        vcap = cv.VideoCapture(video_input_path)
        video_renderer = VideoRenderer(
            line_placement_ratio=self.algorithm_config.line_placement_ratio,
            output_path=video_output_path,
            enable_video_writing=enable_video_writing,
            enable_video_showing=enable_video_showing,
            fps=vcap.get(cv.CAP_PROP_FPS),
        )
        centroid_tracker = CentroidTracker(
            max_disappeared=self.algorithm_config.centroid_tracker.max_disappeared,
            max_distance=vcap.get(cv.CAP_PROP_FRAME_HEIGHT)
            / vcap.get(cv.CAP_PROP_FRAME_WIDTH)
            * self.image_width
            * self.algorithm_config.centroid_tracker.max_distance_height_ratio,
        )
        statistics = Statistics()
        trackable_objects: Dict[int, TrackableObject] = {}
        trackers: List[dlib.correlation_tracker] = []
        video_rendering_enabled = enable_video_writing or enable_video_showing
        for frame_number, (time_offset, frame) in enumerate(
            read_video_as_frames(video_input_path, resized_width=self.image_width)
        ):
            drawn_frame = frame.copy()

            if frame_number % self.algorithm_config.inference_periodicity == 0:
                status = Status.DETECTING
                bounding_boxes = self.model.predict(frame)

                trackers: List[dlib.correlation_tracker] = []

                for bounding_box in bounding_boxes:
                    tracker = dlib.correlation_tracker()
                    rectangle = dlib.rectangle(
                        bounding_box.x_min,
                        bounding_box.y_min,
                        bounding_box.x_max,
                        bounding_box.y_max,
                    )
                    tracker.start_track(frame, rectangle)
                    trackers.append(tracker)

                    if video_rendering_enabled:
                        drawn_frame = video_renderer.draw_bounding_box(
                            drawn_frame, bounding_box
                        )

            else:
                status = Status.TRACKING
                bounding_boxes: List[BoundingBox] = []

                for tracker in trackers:
                    tracker.update(frame)
                    tracker_position = tracker.get_position()
                    bounding_box = BoundingBox(
                        x_min=tracker_position.left(),
                        y_min=tracker_position.top(),
                        x_max=tracker_position.right(),
                        y_max=tracker_position.bottom(),
                    )
                    bounding_boxes.append(bounding_box)

                    if video_rendering_enabled:
                        drawn_frame = video_renderer.draw_bounding_box(
                            drawn_frame, bounding_box
                        )

            line_vertical_position = int(
                cfg.algorithm.line_placement_ratio * frame.shape[0]
            )

            objects = centroid_tracker.update(bounding_boxes)

            for object_id, centroid in objects.items():
                tracked_object = trackable_objects.get(object_id)

                if tracked_object is None:
                    tracked_object = TrackableObject(object_id, centroid)

                else:
                    tracked_object.centroids.append(centroid)

                    if not tracked_object.counted:
                        if (
                            centroid[1]
                            < line_vertical_position
                            <= tracked_object.centroids[0][1]
                        ):
                            # statistics.add_went_down(time_offset)
                            statistics.add_went_up(time_offset)
                            tracked_object.counted = True

                        elif (
                            tracked_object.centroids[0][1]
                            <= line_vertical_position
                            < centroid[1]
                        ):
                            # statistics.add_went_up(time_offset)
                            statistics.add_went_down(time_offset)
                            tracked_object.counted = True

                trackable_objects[object_id] = tracked_object

                if video_rendering_enabled:
                    drawn_frame = video_renderer.draw_text(
                        frame=drawn_frame,
                        text=f"ID {object_id}",
                        bottom_left_position=(centroid[0] - 10, centroid[1] - 10),
                    )
                    drawn_frame = video_renderer.draw_circle(
                        frame=drawn_frame, center=(centroid[0], centroid[1])
                    )

            if video_rendering_enabled:
                drawn_frame = video_renderer.draw_statistics(
                    frame=drawn_frame,
                    statistics=statistics,
                    status=status,
                    frame_number=frame_number,
                )
                video_renderer.render(drawn_frame, to_bgr=video_is_rgb_color)

        return statistics, video_renderer
