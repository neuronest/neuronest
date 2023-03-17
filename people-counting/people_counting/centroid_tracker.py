from collections import OrderedDict
from typing import Dict, List

import numpy as np
from scipy.spatial import distance as dist

from people_counting.common import BoundingBox


class CentroidTracker:
    def __init__(self, max_disappeared: int = 50, max_distance: int = 50):
        self.next_object_id = 0
        self.objects: Dict[int, np.ndarray] = OrderedDict()
        self.disappeared: Dict[int, int] = OrderedDict()
        self.max_disappeared = max_disappeared
        self.max_distance = max_distance

    def register(self, centroid: np.ndarray):
        self.objects[self.next_object_id] = centroid
        self.disappeared[self.next_object_id] = 0
        self.next_object_id += 1

    def unregister(self, object_id: int):
        del self.objects[object_id]
        del self.disappeared[object_id]

    # pylint: disable=too-many-locals
    def update(self, bounding_boxes: List[BoundingBox]) -> Dict[int, np.ndarray]:
        if len(bounding_boxes) == 0:
            for object_id in list(self.disappeared.keys()):
                self.disappeared[object_id] += 1

                if self.disappeared[object_id] > self.max_disappeared:
                    self.unregister(object_id)

            return self.objects

        input_centroids = np.zeros((len(bounding_boxes), 2), dtype="int")

        for index, bounding_box in enumerate(bounding_boxes):
            input_centroids[index] = bounding_box.center

        if len(self.objects) == 0:
            for input_centroid in input_centroids:
                self.register(input_centroid)

        else:
            object_ids = list(self.objects)
            object_centroids = [self.objects[key] for key in self.objects]
            distances = dist.cdist(np.array(input_centroids), object_centroids)
            found_objects_input_idx = np.where(
                np.min(distances, axis=1) <= self.max_distance
            )[0]
            found_objects_idx = distances[found_objects_input_idx].argmin(axis=1)
            disappeared_objects_idx = set(range(len(object_centroids))).difference(
                set(found_objects_idx)
            )
            new_inputs_idx = set(range(len(input_centroids))).difference(
                set(found_objects_input_idx)
            )

            for found_object_idx, found_object_input_idx in zip(
                found_objects_idx, found_objects_input_idx
            ):
                object_id = object_ids[found_object_idx]
                self.objects[object_id] = input_centroids[found_object_input_idx]
                self.disappeared[object_id] = 0

            for disappeared_object_idx in disappeared_objects_idx:
                object_id = object_ids[disappeared_object_idx]
                self.disappeared[object_id] += 1

                if self.disappeared[object_id] > self.max_disappeared:
                    self.unregister(object_id)

            for new_input_idx in new_inputs_idx:
                self.register(input_centroids[new_input_idx])

        return self.objects
