FROM python:3.8.14-buster

ARG APP_DIRECTORY="app"
ARG PEOPLE_COUNTING_REPOSITORY="people-counting"

WORKDIR /$APP_DIRECTORY/$PEOPLE_COUNTING_REPOSITORY

# Install python packages
COPY $PEOPLE_COUNTING_REPOSITORY/pyproject.toml $PEOPLE_COUNTING_REPOSITORY/poetry.lock ./
COPY shared /$APP_DIRECTORY/shared

RUN apt update && apt install -y cmake
RUN pip install --upgrade pip \
    && pip install poetry \
    && poetry export --without-hashes --with dev -f requirements.txt --output requirements.txt \
    && pip install -r requirements.txt

# Install opencv dependencies
RUN apt-get install -y python3-opencv

# Add code
COPY . /$APP_DIRECTORY

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True

CMD exec uvicorn api.main:app --host 0.0.0.0 --port 8080 --log-level info --reload