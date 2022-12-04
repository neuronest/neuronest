import os
import shutil
import tempfile
import zipfile

import gdown
from people_counting.config import cfg

if __name__ == "__main__":
    shutil.rmtree(cfg.paths.videos_directory, ignore_errors=True)
    with tempfile.NamedTemporaryFile() as temporary_file:
        gdown.download(cfg.dataset.google_drive_url, temporary_file.name, quiet=False)
        with zipfile.ZipFile(temporary_file.name, "r") as zip_ref:
            os.makedirs(cfg.paths.videos_directory, exist_ok=True)
            zip_ref.extractall(cfg.paths.videos_directory)
    dataset_name = os.listdir(cfg.paths.videos_directory).pop()
    for file in os.listdir(os.path.join(cfg.paths.videos_directory, dataset_name)):
        shutil.move(
            os.path.join(cfg.paths.videos_directory, dataset_name, file),
            os.path.join(cfg.paths.videos_directory, file),
        )
    shutil.rmtree(os.path.join(cfg.paths.videos_directory, dataset_name))
