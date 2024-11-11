FROM python:3.11.10-slim-bookworm

RUN apt -qqy update > /dev/null \
    && apt install -qqy cmake curl ffmpeg python3-opencv > /dev/null

ARG REPOSITORY_NAME
ARG PACKAGE_NAME
ARG ROOT_DIRECTORY="/app"
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

ENV POETRY_HOME="/opt/poetry"
ENV PATH="$POETRY_HOME/bin:$ROOT_DIRECTORY/$REPOSITORY_NAME/.venv/bin:$PATH"

COPY $SHARED_REPOSITORY_NAME $ROOT_DIRECTORY/$SHARED_REPOSITORY_NAME

WORKDIR $ROOT_DIRECTORY/$REPOSITORY_NAME

COPY $REPOSITORY_NAME/pyproject.toml $REPOSITORY_NAME/poetry.lock ./
RUN curl -sSL https://install.python-poetry.org | python

RUN poetry config virtualenvs.in-project true \
    && poetry config virtualenvs.path $ROOT_DIRECTORY/$REPOSITORY_NAME/.venv \
    && poetry config virtualenvs.create true \
    && poetry check  \
    && poetry install --with app \
    && rm -rf /root/.cache/pypoetry

COPY $REPOSITORY_NAME/conf/ conf
COPY $REPOSITORY_NAME/$PACKAGE_NAME $PACKAGE_NAME

EXPOSE $PORT

CMD gunicorn \
    --workers $WORKERS \
    --timeout $TIMEOUT \
    --access-logfile - \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:$PORT \
    $PACKAGE_NAME.app.main:app
