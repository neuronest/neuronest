FROM nvidia/cuda:12.0.0-runtime-ubuntu20.04 as training

RUN apt-get -qqy update && apt-get install -qqy software-properties-common
# to get latest python versions
RUN add-apt-repository ppa:deadsnakes/ppa

RUN apt-get -qqy update && apt-get install -qqy \
        build-essential \
        curl \
        ffmpeg \
        git \
        libffi-dev \
        libsm6 \
        libssl-dev \
        libxext6 \
        libxrender-dev \
        python3-crcmod \
        python3-pip \
        python3.8 \
        python3.8-dev \
        uuid-runtime \
        x264

ARG PROJECT_DIRECTORY="object-detection"
ENV PROJECT_DIRECTORY=$PROJECT_DIRECTORY

ENV CLOUDSDK_INSTALL_DIR /usr/local/gcloud
RUN curl -sSL https://sdk.cloud.google.com | bash
ENV PATH $PATH:$CLOUDSDK_INSTALL_DIR/google-cloud-sdk/bin

ENV PYSETUP_PATH="/opt/pysetup"
ENV POETRY_HOME="/opt/poetry"
# using 'poetry config virtualenvs.in-project true' makes the virtualenv in '.venv' at
# the root of the project
ENV VENV_PATH="$PYSETUP_PATH/.venv"
ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"
ENV PYTHONPATH="${PYTHONPATH}:app"

ENV SHARED_PATH="/opt/shared"

# install poetry - respects $POETRY_VERSION & $POETRY_HOME
RUN curl -sSL https://install.python-poetry.org | python3

COPY shared $SHARED_PATH

WORKDIR $PYSETUP_PATH
COPY $PROJECT_DIRECTORY/pyproject.toml $PROJECT_DIRECTORY/poetry.lock ./
RUN poetry config virtualenvs.in-project true
RUN poetry install

RUN mkdir -p /app/object_detection

COPY $PROJECT_DIRECTORY/config.yaml /app
COPY $PROJECT_DIRECTORY/object_detection /app/object_detection

WORKDIR /app/

FROM training as serving
# inspired of https://github.com/GoogleCloudPlatform/vertex-ai-samples/blob/main/community-content/pytorch_text_classification_using_vertex_sdk_and_gcloud/pytorch-text-classification-vertex-ai-train-tune-deploy.ipynb

COPY --from=ultralytics/yolov5:latest /usr/src/app/models /app/model/models
COPY --from=ultralytics/yolov5:latest /usr/src/app/utils /app/model/utils

RUN apt-get -qqy update && apt-get install -qqy \
        wget \
        libsndfile1 \
        libsndfile1-dev \
        zip

RUN apt-get install -y openjdk-11-jdk

ARG MODEL_PATH

RUN mkdir /model
ENV LOCAL_MODEL_PATH="/model/model.pt"

WORKDIR /app/model/

COPY $PROJECT_DIRECTORY/object_detection/model_handler.py .
COPY $PROJECT_DIRECTORY/object_detection/modules modules
COPY $PROJECT_DIRECTORY/object_detection/config.py .
COPY $PROJECT_DIRECTORY/config.yaml .

COPY $MODEL_PATH $LOCAL_MODEL_PATH

RUN curl -sSL https://raw.githubusercontent.com/pytorch/serve/master/docker/dockerd-entrypoint.sh > ./dockerd-entrypoint.sh
RUN chmod +x dockerd-entrypoint.sh

# create torchserve configuration file
RUN printf "\nservice_envelope=json" >> ./config.properties
RUN printf "\ninference_address=http://0.0.0.0:7080" >> ./config.properties
RUN printf "\nmanagement_address=http://0.0.0.0:7081" >> ./config.properties

# expose health and prediction listener ports from the image
EXPOSE 7080
EXPOSE 7081

RUN mkdir -p model_store

# create model archive file packaging model artifacts and dependencies
RUN torch-model-archiver -f \
  --model-name=object_detection \
  --version=1.0 \
  --serialized-file=$LOCAL_MODEL_PATH \
  --handler=model_handler.py \
  --extra-files=modules,config.py,config.yaml \
  --export-path=model_store

RUN zip -ur model_store/object_detection.mar models
RUN zip -ur model_store/object_detection.mar utils

ENTRYPOINT ["./dockerd-entrypoint.sh"]

# run Torchserve HTTP serve to respond to prediction requests
CMD ["torchserve", \
     "--start", \
     "--ts-config=config.properties", \
     "--models", \
     "object_detection=object_detection.mar", \
     "--model-store", \
     "model_store"]
