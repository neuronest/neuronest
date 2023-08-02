FROM nvidia/cuda:12.0.0-runtime-ubuntu20.04 as training

RUN apt -qqy update  \
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
        python3-crcmod \
        python3-pip \
        python3.8 \
        python3.8-dev \
        software-properties-common \
        uuid-runtime \
        wget \
        x264 \
        zip

ARG REPOSITORY_NAME
ARG PACKAGE_NAME
ARG MODEL_NAME
RUN echo "The value of MODEL_NAME is: $MODEL_NAME"
ARG ROOT_DIRECTORY="/app"
ARG SHARED_REPOSITORY_NAME="shared"
ARG POETRY_VERSION="1.3.2"

ENV PIP_ROOT_USER_ACTION=ignore
ENV REPOSITORY_NAME=$REPOSITORY_NAME
ENV PACKAGE_NAME=$PACKAGE_NAME
ENV MODEL_NAME=$MODEL_NAME
RUN echo "The value of MODEL_NAME is: $MODEL_NAME"
ENV ROOT_DIRECTORY=$ROOT_DIRECTORY
ENV SHARED_REPOSITORY_NAME=$SHARED_REPOSITORY_NAME
ENV POETRY_VERSION=$POETRY_VERSION

ENV POETRY_HOME="/opt/poetry"
ENV PATH="$POETRY_HOME/bin:$ROOT_DIRECTORY/$REPOSITORY_NAME/.venv/bin:$PATH"

ENV CLOUDSDK_INSTALL_DIR=/usr/local/gcloud
RUN curl -sSL https://sdk.cloud.google.com | bash
ENV PATH=$PATH:$CLOUDSDK_INSTALL_DIR/google-cloud-sdk/bin

COPY $SHARED_REPOSITORY_NAME $ROOT_DIRECTORY/$SHARED_REPOSITORY_NAME
WORKDIR $ROOT_DIRECTORY/$REPOSITORY_NAME

COPY $REPOSITORY_NAME/pyproject.toml $REPOSITORY_NAME/poetry.lock ./
# using 'poetry config virtualenvs.in-project true' makes the virtualenv in '.venv' at
# the root of the project
RUN curl -sSL https://install.python-poetry.org | python3
RUN poetry config virtualenvs.in-project true \
    && poetry config virtualenvs.create true \
    && poetry check  \
    && poetry install

# COPY $REPOSITORY_NAME/config.yaml .
COPY $REPOSITORY_NAME/$PACKAGE_NAME $PACKAGE_NAME


FROM training as serving
# inspired of https://github.com/GoogleCloudPlatform/vertex-ai-samples/blob/main/community-content/pytorch_text_classification_using_vertex_sdk_and_gcloud/pytorch-text-classification-vertex-ai-train-tune-deploy.ipynb

ARG MODEL_PATH
ARG LOCAL_MODEL_PATH="/model/model.pt"
ARG MODEL_STORE_NAME="model_store"
ARG MODEL_PACKAGE_NAME="model"
ARG MODEL_PACKAGE_PATH=$ROOT_DIRECTORY/$REPOSITORY_NAME/$MODEL_PACKAGE_NAME

ENV LOCAL_MODEL_PATH=$LOCAL_MODEL_PATH
ENV MODEL_STORE_NAME=$MODEL_STORE_NAME
ENV MODEL_PACKAGE_NAME=$MODEL_PACKAGE_NAME
ENV MODEL_PACKAGE_PATH=$MODEL_PACKAGE_PATH

RUN mkdir $MODEL_PACKAGE_NAME

# I think it is no more used, see _load_hub_pretrained_model instead
#RUN mkdir tmp \
#    && wget -O master.zip https://github.com/ultralytics/yolov5/zipball/master \
#    && bsdtar --strip-components=1 -xvf master.zip -C tmp \
#    && mv tmp/models tmp/utils $MODEL_PACKAGE_NAME \
#    && rm -r master.zip tmp

#RUN cp -r \
#    $PACKAGE_NAME/model_handler.py  \
#    $PACKAGE_NAME/modules  \
#    $PACKAGE_NAME/config.py \
#    $PACKAGE_NAME/config.yaml \
#    $MODEL_PACKAGE_NAME

RUN cp -r $PACKAGE_NAME $MODEL_PACKAGE_NAME

WORKDIR $MODEL_PACKAGE_PATH

# create torchserve configuration file
RUN printf "\nservice_envelope=json" >> config.properties
RUN printf "\ninference_address=http://0.0.0.0:7080" >> config.properties
RUN printf "\nmanagement_address=http://0.0.0.0:7081" >> config.properties

# expose health and prediction listener ports from the image
EXPOSE 7080
EXPOSE 7081

RUN mkdir -p $MODEL_STORE_NAME

COPY $MODEL_PATH $LOCAL_MODEL_PATH

# copy of the solution proposed so that the archive respects the hierarchy of the
# project, whereas by default all the files are placed at the same level in the archive,
# leading to a break in the import logic between the package vs what happens
# when from torchserve. See: https://github.com/pytorch/serve/issues/566#issuecomment-964340770
ENV TMP_PACKAGE_DIR=/tmp/${PACKAGE_NAME}_tmp
RUN mkdir $TMP_PACKAGE_DIR
RUN cp -r $PACKAGE_NAME $TMP_PACKAGE_DIR
# RUN ln -s $MODEL_PACKAGE_PATH $TEMP_PACKAGE_DIR

# create model archive file packaging model artifacts and dependencies
RUN torch-model-archiver -f \
  --model-name=$MODEL_NAME \
  --version=1.0 \
  --serialized-file=$LOCAL_MODEL_PATH \
  --handler=$MODEL_PACKAGE_PATH/$PACKAGE_NAME/model_handler.py \
  --extra-files=$TMP_PACKAGE_DIR \
  --export-path=$MODEL_STORE_NAME

# RUN rm -rf $TEMP_PACKAGE_DIR

# ENV TORCH_MODEL_ARCHIVER_MODEL_MAR_PATH=$MODEL_STORE_NAME/$MODEL_NAME.mar

# I think it is no more used, since _load_hub_pretrained_model is used instead
#RUN zip -ur $TORCH_MODEL_ARCHIVER_MODEL_MAR_PATH models \
#  && zip -ur $TORCH_MODEL_ARCHIVER_MODEL_MAR_PATH utils

# run Torchserve HTTP serve to respond to prediction requests
ENTRYPOINT torchserve \
    --start \
    --ts-config=config.properties \
    --models $MODEL_NAME=$MODEL_NAME.mar \
    --model-store $MODEL_STORE_NAME \
    && tail -f /dev/null  # to prevent docker exit, as torchserve runs in background
