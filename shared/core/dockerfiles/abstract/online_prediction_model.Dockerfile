FROM nvidia/cuda:12.5.0-runtime-ubuntu22.04 as training

RUN apt -qqy update > /dev/null \
&& apt install -qqy software-properties-common > /dev/null \
&& add-apt-repository ppa:deadsnakes/ppa \
&& DEBIAN_FRONTEND=noninteractive apt install -qqy \
        build-essential \
        curl \
        ffmpeg \
        git \
        libarchive-tools \
        libffi-dev \
        libsm6 \
        libsndfile1 \
        libsndfile1-dev \
        libssl-dev \
        libxext6 \
        libxrender-dev \
        openjdk-11-jdk \
        uuid-runtime \
        wget \
        x264 \
        zip > /dev/null

# Install Python 3.11
RUN apt -qqy update > /dev/null && DEBIAN_FRONTEND=noninteractive apt install -qqy python3.11 python3.11-dev python3.11-distutils > /dev/null

# Install pip for Python 3.11
RUN wget https://bootstrap.pypa.io/get-pip.py && python3.11 get-pip.py

ARG REPOSITORY_NAME
RUN if [ -z "$REPOSITORY_NAME" ]; then echo "REPOSITORY_NAME is not set" && exit 1; fi
ARG PACKAGE_NAME
RUN if [ -z "$PACKAGE_NAME" ]; then echo "PACKAGE_NAME is not set" && exit 1; fi
ARG MODEL_NAME
RUN if [ -z "$MODEL_NAME" ]; then echo "MODEL_NAME is not set" && exit 1; fi
ARG BATCH_SIZE
RUN if [ -z "$BATCH_SIZE" ]; then echo "BATCH_SIZE is not set" && exit 1; fi
ARG POETRY_VERSION
RUN if [ -z "$POETRY_VERSION" ]; then echo "POETRY_VERSION is not set" && exit 1; fi
ARG ROOT_DIRECTORY="/app"
ARG SHARED_REPOSITORY_NAME="shared"
ARG MAX_BATCH_DELAY="50"

ENV PIP_ROOT_USER_ACTION=ignore
ENV REPOSITORY_NAME=$REPOSITORY_NAME
ENV PACKAGE_NAME=$PACKAGE_NAME
ENV MODEL_NAME=$MODEL_NAME
ENV ROOT_DIRECTORY=$ROOT_DIRECTORY
ENV SHARED_REPOSITORY_NAME=$SHARED_REPOSITORY_NAME
ENV POETRY_VERSION=$POETRY_VERSION
ENV BATCH_SIZE=$BATCH_SIZE
ENV MAX_BATCH_DELAY=$MAX_BATCH_DELAY

ENV POETRY_HOME="/opt/poetry"
ENV PATH="$POETRY_HOME/bin:$ROOT_DIRECTORY/$REPOSITORY_NAME/.venv/bin:$PATH"

ENV CLOUDSDK_INSTALL_DIR=/usr/local/gcloud
RUN curl -sSL https://sdk.cloud.google.com | bash > /dev/null 2>&1  # silent logs
ENV PATH=$PATH:$CLOUDSDK_INSTALL_DIR/google-cloud-sdk/bin

RUN mkdir -p $ROOT_DIRECTORY/$SHARED_REPOSITORY_NAME
COPY $SHARED_REPOSITORY_NAME/pyproject.toml $SHARED_REPOSITORY_NAME/poetry.lock $ROOT_DIRECTORY/$SHARED_REPOSITORY_NAME/
COPY $SHARED_REPOSITORY_NAME/core $ROOT_DIRECTORY/$SHARED_REPOSITORY_NAME/core

COPY $SHARED_REPOSITORY_NAME $ROOT_DIRECTORY/$SHARED_REPOSITORY_NAME

WORKDIR $ROOT_DIRECTORY/$REPOSITORY_NAME

# make python3.11 the default
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 2
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.11 2

COPY $REPOSITORY_NAME/pyproject.toml $REPOSITORY_NAME/poetry.lock ./
RUN curl -sSL https://install.python-poetry.org | python

RUN poetry env use python \
    && poetry config virtualenvs.in-project true \
    && poetry config virtualenvs.path $ROOT_DIRECTORY/$REPOSITORY_NAME/.venv \
    && poetry config virtualenvs.create true \
    && poetry check  \
    && poetry install --with model \
    && rm -rf /root/.cache/pypoetry

COPY $REPOSITORY_NAME/conf/ conf
COPY $REPOSITORY_NAME/$PACKAGE_NAME $PACKAGE_NAME


FROM training as serving
# inspired of https://github.com/GoogleCloudPlatform/vertex-ai-samples/blob/main/community-content/pytorch_text_classification_using_vertex_sdk_and_gcloud/pytorch-text-classification-vertex-ai-train-tune-deploy.ipynb

ARG MODEL_PATH
RUN if [ -z "$MODEL_PATH" ]; then echo "MODEL_PATH is not set" && exit 1; fi
ARG LOCAL_MODEL_PATH="/model/model.pt"
ARG MODEL_STORE_NAME="model_store"
ARG MODEL_PACKAGE_NAME="model/"
ARG MODEL_PACKAGE_PATH=$ROOT_DIRECTORY/$REPOSITORY_NAME/$MODEL_PACKAGE_NAME

ENV LOCAL_MODEL_PATH=$LOCAL_MODEL_PATH
ENV MODEL_STORE_NAME=$MODEL_STORE_NAME
ENV MODEL_PACKAGE_NAME=$MODEL_PACKAGE_NAME
ENV MODEL_PACKAGE_PATH=$MODEL_PACKAGE_PATH

RUN mkdir $MODEL_PACKAGE_NAME
RUN cp -r $PACKAGE_NAME conf $MODEL_PACKAGE_NAME
WORKDIR $MODEL_PACKAGE_PATH

# create torchserve configuration file
RUN printf "\nservice_envelope=json" >> config.properties
RUN printf "\ninference_address=http://0.0.0.0:7080" >> config.properties
RUN printf "\nmanagement_address=http://0.0.0.0:7081" >> config.properties
RUN printf '\nmodels={"%s": {"1.0": {"batchSize": %s,"maxBatchDelay": %s}}}' "$MODEL_NAME" "1" "$MAX_BATCH_DELAY" >> config.properties
RUN printf "\nmin_worker=1" >> config.properties
RUN printf "\ninitial_workers=1" >> config.properties
RUN printf "\nmax_worker=1" >> config.properties

# expose health and prediction listener ports from the image
EXPOSE 7080
EXPOSE 7081

RUN mkdir -p $MODEL_STORE_NAME

COPY $MODEL_PATH $LOCAL_MODEL_PATH

ENV TMP_PACKAGE_DIR=/tmp/$PACKAGE_NAME/
RUN mkdir $TMP_PACKAGE_DIR
RUN cp -r $PACKAGE_NAME conf $TMP_PACKAGE_DIR

# create model archive file packaging model artifacts and dependencies
RUN torch-model-archiver -f \
  --model-name=$MODEL_NAME \
  --version=1.0 \
  --serialized-file=$LOCAL_MODEL_PATH \
  --handler=$MODEL_PACKAGE_PATH/$PACKAGE_NAME/model_handler.py \
  --extra-files=$TMP_PACKAGE_DIR \
  --export-path=$MODEL_STORE_NAME

# run Torchserve HTTP serve to respond to prediction requests
ENTRYPOINT torchserve \
    --start \
    # see https://github.com/pytorch/serve/blob/master/docs/token_authorization_api.md
    --disable-token-auth \
    --ts-config=config.properties \
    --models $MODEL_NAME=$MODEL_NAME.mar \
    --model-store $MODEL_STORE_NAME \
    && tail -f /dev/null  # to prevent docker exit, as torchserve runs in background
