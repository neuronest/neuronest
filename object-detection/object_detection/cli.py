from core.packages.abstract.online_prediction_model.cli import main as cli_main

from object_detection.config import cfg

if __name__ == "__main__":
    cli_main(config=cfg)
