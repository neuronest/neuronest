import os

GOOGLE_APPLICATION_CREDENTIALS = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
SERVICE_ACCOUNT_EMAIL = os.environ.get("SERVICE_ACCOUNT_EMAIL")
TRAINING_IMAGE_NAME = os.environ.get("TRAINING_IMAGE_NAME")
PROJECT_ID = os.environ.get("PROJECT_ID")
REGION = os.environ.get("REGION")
# MODEL_INSTANTIATOR_HOST represents the linking of two services and cannot be expected
# to be known as an environment variable in all contexts, such as a train for example
MODEL_INSTANTIATOR_HOST = os.environ.get("MODEL_INSTANTIATOR_HOST")
