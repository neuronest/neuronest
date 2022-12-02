import numpy as np


# pylint: disable=too-few-public-methods
class TrackableObject:
    def __init__(self, object_id: int, centroid: np.ndarray):
        self.object_id = object_id
        self.centroids = [centroid]
        self.counted = False
