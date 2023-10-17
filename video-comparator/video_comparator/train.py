from core.packages.abstract.online_prediction_model.train import main as train_main

from video_comparator.config import cfg
from video_comparator.modules.model import VideoComparatorModel

if __name__ == "__main__":
    model = VideoComparatorModel()
    train_main(online_prediction_model=model, config=cfg)
