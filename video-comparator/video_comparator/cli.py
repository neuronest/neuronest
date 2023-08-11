from core.packages.abstract.online_prediction_model.cli import main as cli_main

from video_comparator.config import cfg

if __name__ == "__main__":
    cli_main(config=cfg)
