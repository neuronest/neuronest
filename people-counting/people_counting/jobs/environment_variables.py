import os

PROJECT_ID = os.environ["PROJECT_ID"]
REGION = os.environ["REGION"]

OBJECT_DETECTION_MODEL_NAME = os.environ["OBJECT_DETECTION_MODEL_NAME"]
MODEL_INSTANTIATOR_HOST = os.environ["MODEL_INSTANTIATOR_HOST"]
FIRESTORE_RESULTS_COLLECTION = os.environ["FIRESTORE_RESULTS_COLLECTION"]

JOB_ID = os.environ["JOB_ID"]
ASSET_ID = os.environ["ASSET_ID"]
VIDEO_STORAGE_PATH = os.environ["VIDEO_STORAGE_PATH"]
COUNTED_VIDEO_STORAGE_PATH = os.environ.get("COUNTED_VIDEO_STORAGE_PATH")
