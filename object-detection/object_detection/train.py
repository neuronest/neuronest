from core.packages.abstract.online_prediction_model.train import main as train_main

from object_detection.config import cfg
from object_detection.modules.model import ObjectDetectionModel

if __name__ == "__main__":
    model = ObjectDetectionModel(
        model_type=cfg.model.inner_model_type,
        model_name=cfg.model.inner_model_name,
        retrieve_remote_model=True,
    )
    train_main(online_prediction_model=model, config=cfg)
