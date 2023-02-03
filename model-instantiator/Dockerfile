FROM python:3.8.14-buster

RUN apt update && apt install -y cmake

ARG ROOT_DIRECTORY="/app"
ARG PROJECT_DIRECTORY="model-instantiator"
ARG SHARED_DIRECTORY="shared"

ENV PIP_ROOT_USER_ACTION=ignore
ENV ROOT_DIRECTORY=$ROOT_DIRECTORY
ENV PROJECT_DIRECTORY=$PROJECT_DIRECTORY
ENV SHARED_DIRECTORY=$SHARED_DIRECTORY

COPY shared $ROOT_DIRECTORY/$SHARED_DIRECTORY
WORKDIR $ROOT_DIRECTORY/$PROJECT_DIRECTORY

COPY $PROJECT_DIRECTORY/pyproject.toml $PROJECT_DIRECTORY/poetry.lock ./
RUN pip install --upgrade pip \
  && pip install poetry \
  && poetry export --without-hashes -f requirements.txt --output requirements.txt \
  && pip install -r requirements.txt

COPY $PROJECT_DIRECTORY/conf/ conf
COPY $PROJECT_DIRECTORY/model_instantiator model_instantiator

EXPOSE 80

CMD ["gunicorn", "--workers", "4", \
                 "--timeout", "300", \
                 "--access-logfile", "-", \
                 "--worker-class", "uvicorn.workers.UvicornWorker", \
                 "--bind", "0.0.0.0:80", \
                 "model_instantiator.api.main:app"]
