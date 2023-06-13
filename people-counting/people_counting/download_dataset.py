import os
import shutil
import tempfile
import zipfile

import gdown

from people_counting.config import config

if __name__ == "__main__":
    shutil.rmtree(config.paths.videos_directory, ignore_errors=True)

    with tempfile.NamedTemporaryFile() as temporary_file:
        gdown.download(
            config.dataset.google_drive_url, temporary_file.name, quiet=False
        )
        with zipfile.ZipFile(temporary_file.name, "r") as zip_ref:
            os.makedirs(config.paths.videos_directory, exist_ok=True)
            zip_ref.extractall(config.paths.videos_directory)

    dataset_name = os.listdir(config.paths.videos_directory).pop()

    for file in os.listdir(os.path.join(config.paths.videos_directory, dataset_name)):
        shutil.move(
            os.path.join(config.paths.videos_directory, dataset_name, file),
            os.path.join(config.paths.videos_directory, file),
        )
    shutil.rmtree(os.path.join(config.paths.videos_directory, dataset_name))
