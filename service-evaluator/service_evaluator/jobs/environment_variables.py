import os

GOOGLE_APPLICATION_CREDENTIALS = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
PROJECT_ID = os.environ["PROJECT_ID"]
REGION = os.environ["REGION"]
REUSE_ALREADY_COMPUTED_RESULTS = os.environ["REUSE_ALREADY_COMPUTED_RESULTS"]
SERIALIZED_SERVICE_CLIENT_PARAMETERS = os.environ[
    "SERIALIZED_SERVICE_CLIENT_PARAMETERS"
]
SERVICE_NAME = os.environ["SERVICE_NAME"]
SERVICE_IMAGE_NAME = os.environ["SERVICE_IMAGE_NAME"]
