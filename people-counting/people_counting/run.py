import argparse
import logging
import os

from people_counting.common import init_logger
from people_counting.config import cfg
from people_counting.people_counter import PeopleCounter

init_logger(logging.INFO)
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument(
        "-i", "--input-video", action="store", type=str, required=True
    )
    args = argument_parser.parse_args()

    if not os.path.exists(args.input_video):
        raise FileNotFoundError(
            f"The video path specified does not exist: '{args.input_video}'"
        )

    people_counter = PeopleCounter(
        model_config=cfg.model,
        algorithm_config=cfg.algorithm,
        image_width=cfg.preprocessing.image_width,
        video_outputs_directory=cfg.paths.outputs_directory,
    )
    prediction, _ = people_counter.run(
        args.input_video,
        enable_video_writing=cfg.general.enable_video_writing,
        enable_video_showing=cfg.general.enable_video_showing,
    )

    if people_counter.run_duration is not None:
        logger.info(f"Elapsed time: {people_counter.run_duration['run']}s")

    output_file = os.path.join(
        cfg.paths.outputs_directory,
        os.path.basename(os.path.splitext(args.input_video)[0]) + ".csv",
    )
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    prediction.to_csv(output_file, index=False)
