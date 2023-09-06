FROM python:3.8.14-buster

RUN apt -qqy update && apt install -y cmake ffmpeg python3-opencv

ARG ROOT_DIRECTORY="/app"
ARG REPOSITORY_NAME="people-counting"
ARG PACKAGE_NAME="people_counting"
ARG SHARED_REPOSITORY_NAME="shared"
ARG PORT=80
ARG WORKERS=4
ARG TIMEOUT=300

ENV PIP_ROOT_USER_ACTION=ignore
ENV ROOT_DIRECTORY=$ROOT_DIRECTORY
ENV REPOSITORY_NAME=$REPOSITORY_NAME
ENV PACKAGE_NAME=$PACKAGE_NAME
ENV SHARED_REPOSITORY_NAME=$SHARED_REPOSITORY_NAME
ENV PORT=$PORT
ENV WORKERS=$WORKERS
ENV TIMEOUT=$TIMEOUT
ENV PYTHONUNBUFFERED True

COPY $SHARED_REPOSITORY_NAME $ROOT_DIRECTORY/$SHARED_REPOSITORY_NAME
WORKDIR $ROOT_DIRECTORY/$REPOSITORY_NAME

COPY $REPOSITORY_NAME/pyproject.toml $REPOSITORY_NAME/poetry.lock ./
RUN pip install --upgrade pip \
  && pip install poetry \
  && poetry export --without-hashes -f requirements.txt --output requirements.txt \
  && pip install -r requirements.txt

COPY $REPOSITORY_NAME/conf/ conf
COPY $REPOSITORY_NAME/$PACKAGE_NAME $PACKAGE_NAME

EXPOSE $PORT

CMD gunicorn \
    --workers $WORKERS \
    --timeout $TIMEOUT \
    --access-logfile - \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:$PORT \
    $PACKAGE_NAME.api.main:app
