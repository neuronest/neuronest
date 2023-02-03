FROM python:3.8.14-buster

RUN apt update && apt install -y cmake

ARG PROJECT_DIRECTORY="model-instantiator"
ENV PROJECT_DIRECTORY=$PROJECT_DIRECTORY

ENV PYSETUP_PATH="/opt/pysetup"
ENV POETRY_HOME="/opt/poetry"
# using 'poetry config virtualenvs.in-project true' makes the virtualenv in '.venv' at
# the root of the project
ENV VENV_PATH="$PYSETUP_PATH/.venv"
ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"
ENV PYTHONPATH="${PYTHONPATH}:app"

ENV SHARED_PATH="/opt/shared"

# install poetry - respects $POETRY_VERSION & $POETRY_HOME
RUN curl -sSL https://install.python-poetry.org | python

COPY shared $SHARED_PATH

WORKDIR $PYSETUP_PATH
COPY $PROJECT_DIRECTORY/pyproject.toml $PROJECT_DIRECTORY/poetry.lock ./
RUN poetry config virtualenvs.in-project true
RUN poetry install

RUN mkdir -p /app/model_instantiator /app/conf

COPY $PROJECT_DIRECTORY/conf/ /app/conf
COPY $PROJECT_DIRECTORY/model_instantiator /app/model_instantiator

EXPOSE 80
WORKDIR /app/

CMD ["gunicorn", "--workers", "4", \
                 "--timeout", "300", \
                 "--access-logfile", "-", \
                 "--worker-class", "uvicorn.workers.UvicornWorker", \
                 "--bind", "0.0.0.0:80", \
                 "model_instantiator.api.main:app"]
