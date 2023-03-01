import argparse
import logging
import os
from typing import List, Optional

import pandas as pd
from people_counting.common import VIDEOS_EXTENSIONS, init_logger
from people_counting.config import cfg
from people_counting.dependencies import get_people_counter_with_package_config

init_logger(logging.INFO)
logger = logging.getLogger(__name__)


def predict_all(
    videos_directory: str, output_file: Optional[str] = None
) -> pd.DataFrame:
    # pylint: disable=duplicate-code
    people_counter = get_people_counter_with_package_config()
    predictions: List[pd.DataFrame] = []

    for video_file in filter(
        lambda file: any(file.endswith(extension) for extension in VIDEOS_EXTENSIONS),
        os.listdir(videos_directory),
    ):
        input_video = os.path.join(cfg.paths.videos_directory, video_file)
        prediction, _ = people_counter.run(
            input_video,
            enable_video_writing=cfg.general.enable_video_writing,
            enable_video_showing=cfg.general.enable_video_showing,
        )
        prediction = prediction.to_df()
        predictions.append(
            pd.concat(
                [
                    pd.DataFrame(
                        columns=["video"], data=[video_file] * len(prediction)
                    ),
                    prediction,
                ],
                axis=1,
            )
        )

        if people_counter.run_duration is not None:
            logger.info(
                f"Elapsed time for {input_video}: {people_counter.run_duration['run']}s"
            )

    predictions: pd.DataFrame = pd.concat(predictions, axis=0)

    if output_file is not None:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        predictions.to_csv(output_file, index=False)

    return predictions


def mae(pred_in: int, pred_out: int, true_in: int, true_out: int) -> int:
    return abs(pred_in - true_in) + abs(pred_out - true_out)


def compute_score(
    labels: pd.DataFrame, predictions: pd.DataFrame, output_file: Optional[str] = None
) -> pd.DataFrame:
    scores = {}
    predictions["count"] = predictions["count"].astype(int)
    labels["in"], labels["out"] = labels["in"].astype(int), labels["out"].astype(int)

    for video_file in set(labels["video"]):
        prediction = predictions[predictions["video"] == video_file]
        pred_in, pred_out = sum(prediction["count"] == 1), sum(
            prediction["count"] == -1
        )
        label = labels[labels["video"] == video_file]
        true_in, true_out = label["in"].item(), label["out"].item()

        score = mae(pred_in, pred_out, true_in, true_out)
        scores[video_file] = score

    scores_results = pd.DataFrame(
        index=scores.keys(), data=scores.values()
    ).reset_index()
    scores_results.columns = ["video", "score"]

    if output_file is not None:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        scores_results.to_csv(output_file, index=False)

    return scores_results


def benchmark():
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument("--skip-predictions-computing", action="store_true")
    args = argument_parser.parse_args()

    labels = pd.read_csv(cfg.paths.labels)

    if args.skip_predictions_computing is True:
        if not os.path.exists(cfg.paths.benchmark):
            raise FileNotFoundError(f"Predictions not found at {cfg.paths.benchmark}")

        predictions = pd.read_csv(cfg.paths.benchmark)
    else:
        predictions = predict_all(
            cfg.paths.videos_directory, output_file=cfg.paths.benchmark
        )

    scores = compute_score(labels, predictions, output_file=cfg.paths.scores)
    logger.info(f"Average MAE: {round(scores.score.values.mean(), 4)}")


if __name__ == "__main__":
    benchmark()
