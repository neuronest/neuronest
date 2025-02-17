FROM python:3.11.10-slim-bookworm

RUN apt -qqy update && apt install -qqy cmake

ARG POETRY_VERSION
ARG ROOT_DIRECTORY="/app"
ARG REPOSITORY_NAME="database-api"
ARG PACKAGE_NAME="database_api"
ARG SHARED_REPOSITORY_NAME="shared"
ARG PORT=80
ARG WORKERS=4
ARG TIMEOUT=300

ENV POETRY_VERSION=$POETRY_VERSION
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
# --no-deps so Poetry is the sole manager of dependencies
RUN pip install --upgrade pip \
  && pip install poetry==$POETRY_VERSION \
  && poetry export --without-hashes -f requirements.txt --output requirements.txt \
  && pip install -r requirements.txt

# COPY $REPOSITORY_NAME/conf/ conf
COPY $REPOSITORY_NAME $ROOT_DIRECTORY/$REPOSITORY_NAME

EXPOSE $PORT

CMD gunicorn \
    --workers $WORKERS \
    --timeout $TIMEOUT \
    --access-logfile - \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:$PORT \
    $PACKAGE_NAME.api.main:app
