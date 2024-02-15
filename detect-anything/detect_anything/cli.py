from core.packages.abstract.online_prediction_model.cli import main as cli_main
from detect_anything.config import cfg

if __name__ == "__main__":
    cli_main(config=cfg)
