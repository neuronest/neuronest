from core.routes.base import BaseResources, _BaseRoutes


class _VideoComparatorRoutes(_BaseRoutes):
    service_name: str = "video_comparator"

    class Resources(BaseResources):
        videos_to_compare_bucket: str = "/videos_to_compare_bucket"
        maximum_videos_number: str = "/maximum_videos_number"

    class VideoComparator:
        prefix = "video_comparator"
        compare_videos: str = "/compare_videos"
        compare_videos_real_time: str = "/compare_videos_real_time"


routes: _VideoComparatorRoutes = _VideoComparatorRoutes()
