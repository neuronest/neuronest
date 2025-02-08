from core.routes.base import BaseResources, _BaseRoutes


class _ObjectDetectionRoutes(_BaseRoutes):
    service_name: str = "object_detection"

    class Resources(BaseResources):
        pass

    class ObjectDetection:
        prefix = "object_detection"
        detect_objects: str = "/detect_objects"
        detect_objects_real_time: str = "/detect_objects_real_time"


routes: _ObjectDetectionRoutes = _ObjectDetectionRoutes()
