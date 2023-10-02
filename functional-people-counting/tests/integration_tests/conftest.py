import os
from typing import Optional

import pytest


@pytest.fixture
def people_counting_url() -> str:
    return os.environ["PEOPLE_COUNTING_URL"]


@pytest.fixture
def project_id() -> str:
    return os.environ["PROJECT_ID"]


@pytest.fixture
def google_application_credentials() -> Optional[str]:
    return os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
