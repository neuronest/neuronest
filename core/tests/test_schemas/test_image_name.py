import pytest

from neuronest.core.schemas.environment import Environment
from neuronest.core.schemas.image_name import (
    BaseImageName,
    ImageName,
    ImageNameWithTag,
    Tag,
)


@pytest.fixture(name="region")
def fixture_region() -> str:
    return "europe-west9"


@pytest.fixture(name="registry_domain")
def fixture_registry_domain(region: str) -> str:
    return ImageName.build_registry_domain(region)


@pytest.fixture(name="project_id")
def fixture_project_id() -> str:
    return "example-project-id"


@pytest.fixture(name="repository_id")
def fixture_repository_id() -> str:
    return "1234567654345"


@pytest.fixture(name="environment")
def fixture_environment() -> Environment:
    return Environment("test")


@pytest.fixture(name="base_image_name")
def fixture_base_image_name() -> BaseImageName:
    return BaseImageName("example-project")


@pytest.fixture(name="tag")
def fixture_tag() -> Tag:
    return Tag("565726992")


def test_image_name(
    registry_domain: str,
    project_id: str,
    region: str,
    repository_id: str,
    base_image_name: BaseImageName,
    environment: Environment,
):
    image_name = ImageName(
        f"{registry_domain}/{project_id}/{repository_id}/"
        f"{base_image_name}/{environment}"
    )

    assert image_name == ImageName.build(
        project_id=project_id,
        region=region,
        repository_id=repository_id,
        base_image_name=base_image_name,
        environment=environment,
    )

    assert image_name.split_base_image_environment() == (base_image_name, environment)


def test_image_name_with_tag(
    registry_domain: str,
    project_id: str,
    region: str,
    repository_id: str,
    base_image_name: BaseImageName,
    environment: Environment,
    tag: Tag,
):
    image_name_with_tag = ImageNameWithTag(
        f"{registry_domain}/{project_id}/{repository_id}/"
        f"{base_image_name}/{environment}:{tag}"
    )

    assert image_name_with_tag == ImageNameWithTag.build(
        project_id=project_id,
        region=region,
        repository_id=repository_id,
        base_image_name=base_image_name,
        environment=environment,
        tag=tag,
    )

    assert image_name_with_tag.split_base_image_environment_and_tag() == (
        base_image_name,
        environment,
        tag,
    )
