from typing import Tuple

from api.model.result import PeopleCounting

from people_counting.people_counter import PeopleCounter


def count_people(
    people_counter: PeopleCounter, video_path: str, write_video: bool = False
) -> Tuple[PeopleCounting, str]:
    predictions, video_renderer = people_counter.run(
        video_path, enable_video_writing=write_video, enable_video_showing=False
    )
    counted_video_path = video_renderer.output_path if write_video else None
    return (
        PeopleCounting.from_counting_statistics(counting_statistics=predictions),
        counted_video_path,
    )
