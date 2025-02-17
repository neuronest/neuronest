from core.routes.base import BaseResources, _BaseRoutes


class _VideoComparatorRoutes(_BaseRoutes):
    service_name: str = "video_comparator"

    class Resources(BaseResources):
        pass

    class VideoComparator:
        prefix = "video_comparator"
        compare_videos: str = "/compare_videos"
        compare_videos_real_time: str = "/compare_videos_real_time"


routes: _VideoComparatorRoutes = _VideoComparatorRoutes()
