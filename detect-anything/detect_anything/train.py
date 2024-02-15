from core.packages.abstract.online_prediction_model.train import main as train_main
from detect_anything.config import cfg
from detect_anything.modules.model import DetectAnythingModel

if __name__ == "__main__":
    model = DetectAnythingModel()
    train_main(online_prediction_model=model, config=cfg)
