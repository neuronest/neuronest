import logging
import os
from typing import Dict, List, Optional

import dlib
from core.client.object_detection import ObjectDetectionClient
from core.schemas.asset import VideoAssetContent
from core.timing import TimingMeta
from imutils import resize
from omegaconf import DictConfig

from people_counting.centroid_tracker import CentroidTracker
from people_counting.common import BoundingBox, Statistics, Status
from people_counting.config import config
from people_counting.model import Model
from people_counting.trackable_object import TrackableObject
from people_counting.video_renderer import VideoRenderer

logger = logging.getLogger(__name__)


class PeopleCounter(metaclass=TimingMeta):
    def __init__(
        self,
        object_detection_client: ObjectDetectionClient,
        algorithm_config: DictConfig,
        image_width: int,
        confidence_threshold: float,
        video_outputs_directory: Optional[str] = None,
    ):
        self.model = Model(
            object_detection_client=object_detection_client,
            confidence_threshold=confidence_threshold,
        )
        self.algorithm_config = algorithm_config
        self.image_width = image_width
        self.video_outputs_directory = video_outputs_directory

        if self.video_outputs_directory is not None:
            os.makedirs(video_outputs_directory, exist_ok=True)

    # pylint: disable=too-many-branches,too-many-locals,too-many-statements
    def run(
        self,
        video_asset_content: VideoAssetContent,
        video_output_path: Optional[str] = None,
        enable_video_showing: bool = False,
        video_is_rgb_color: bool = True,
    ) -> Statistics:
        enable_video_writing = video_output_path is not None
        video_rendering_enabled = enable_video_writing or enable_video_showing

        video_renderer = None
        if video_rendering_enabled is True:
            video_renderer = VideoRenderer(
                line_placement_ratio=self.algorithm_config.line_placement_ratio,
                fps=video_asset_content.asset_meta.fps,
                output_path=video_output_path,
                enable_video_writing=enable_video_writing,
                enable_video_showing=enable_video_showing,
            )

        centroid_tracker = CentroidTracker(
            max_disappeared=self.algorithm_config.centroid_tracker.max_disappeared,
            max_distance=video_asset_content.asset_meta.height
            / video_asset_content.asset_meta.width
            * self.image_width
            * self.algorithm_config.centroid_tracker.max_distance_height_ratio,
        )

        statistics = Statistics()
        trackable_objects: Dict[int, TrackableObject] = {}
        trackers: List[dlib.correlation_tracker] = []

        for frame_number, frame in enumerate(video_asset_content.content):
            time_offset = frame_number * video_asset_content.time_step
            frame = resize(frame, width=self.image_width)
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
                config.algorithm.line_placement_ratio * frame.shape[0]
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
                            statistics.add_went_up(time_offset)
                            tracked_object.counted = True

                        elif (
                            tracked_object.centroids[0][1]
                            <= line_vertical_position
                            < centroid[1]
                        ):
                            statistics.add_went_down(time_offset)
                            tracked_object.counted = True

                trackable_objects[object_id] = tracked_object

                if video_rendering_enabled is True:
                    drawn_frame = video_renderer.draw_bounding_box_id(
                        frame=drawn_frame,
                        object_id=object_id,
                        centroid_x=centroid[0],
                        centroid_y=centroid[1],
                    )

            if video_rendering_enabled is True:
                drawn_frame = video_renderer.draw_statistics_on_frame(
                    frame=drawn_frame,
                    statistics=statistics,
                    status=status,
                    frame_number=frame_number,
                )
                video_renderer.render(drawn_frame, to_bgr=video_is_rgb_color)

        return statistics
