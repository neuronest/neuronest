import os

import pytest


@pytest.fixture
def people_counting_url():
    return os.environ["PEOPLE_COUNTING_URL"]


@pytest.fixture
def project_id():
    return os.environ["PROJECT_ID"]
