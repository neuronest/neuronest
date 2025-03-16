import uuid

import requests
from core.client.database_api import DatabaseApiClient
from core.schemas.modules.database_api import ProjectCreate


# pylint: disable=unused-argument
def test_create_get_and_delete_project(
    database_api_client: DatabaseApiClient,
    uninstantiate_teardown,
):
    gcp_project_id = f"dummy-test-create-delete-{uuid.uuid4()}"

    # Step 1: Create the project
    created_project = database_api_client.create_project(gcp_project_id=gcp_project_id)
    assert created_project.gcp_project_id == gcp_project_id

    # Step 2: Verify the project exists
    fetched_project = database_api_client.get_project(gcp_project_id)
    assert fetched_project.gcp_project_id == gcp_project_id

    # Step 3: Delete the project
    database_api_client.delete_project(gcp_project_id=gcp_project_id)
    try:
        # Attempt to get the project; expect a 404
        database_api_client.get_project(gcp_project_id)
    except requests.exceptions.HTTPError as http_error:
        if http_error.response.status_code == 404:
            # Normal scenario: 404 indicates the project does not exist
            pass
        else:
            # Re-raise for any other HTTP errors
            raise


def test_get_non_existent_project(
    database_api_client: DatabaseApiClient, uninstantiate_teardown
):
    try:
        database_api_client.get_project(f"non-existent-project-{uuid.uuid4()}")
    except requests.exceptions.HTTPError as http_error:
        assert http_error.response.status_code == 404
    else:
        assert False, "Expected HTTPError for non-existent project"


def test_create_duplicate_project(
    database_api_client: DatabaseApiClient, uninstantiate_teardown
):
    project_to_create = ProjectCreate(
        gcp_project_id=f"dummy-duplicate-test-{uuid.uuid4()}"
    )

    # Create the project once
    created_project = database_api_client.create_project(
        gcp_project_id=project_to_create.gcp_project_id
    )
    assert created_project.gcp_project_id == project_to_create.gcp_project_id

    # Attempt to create the project a second time
    try:
        database_api_client.create_project(
            gcp_project_id=project_to_create.gcp_project_id
        )
        # If no error is raised, explicitly fail the test.
        raise AssertionError(
            "Expected HTTPError for duplicate project creation, "
            "but no error was raised."
        )
    except requests.exceptions.HTTPError as http_error:
        # Verify that the error status code is 409 or 400; otherwise, fail the test.
        if http_error.response.status_code not in (409, 400):
            raise AssertionError(
                f"Unexpected HTTP error status: {http_error.response.status_code}"
            ) from http_error

    # Cleanup: Delete the project
    database_api_client.delete_project(gcp_project_id=project_to_create.gcp_project_id)


def test_delete_non_existent_project(
    database_api_client: DatabaseApiClient, uninstantiate_teardown
):
    non_existent_gcp_project_id = f"non-existent-project-to-delete-{uuid.uuid4()}"
    try:
        database_api_client.delete_project(gcp_project_id=non_existent_gcp_project_id)
        raise AssertionError(
            "Expected HTTPError for deletion of non existent project, "
            "but no error was raised."
        )
    except requests.exceptions.HTTPError as http_error:
        # Expecting a 404 Not Found or similar error.
        assert http_error.response.status_code == 404


def test_list_projects(database_api_client: DatabaseApiClient, uninstantiate_teardown):
    project_data = ProjectCreate(gcp_project_id=f"dummy-list-project-{uuid.uuid4()}")
    # Create the project
    database_api_client.create_project(gcp_project_id=project_data.gcp_project_id)

    # List projects and check that the new project is in the list
    projects_list = database_api_client.list_projects()
    project_ids = [project.gcp_project_id for project in projects_list]
    assert project_data.gcp_project_id in project_ids

    # Delete the project
    database_api_client.delete_project(gcp_project_id=project_data.gcp_project_id)

    # List projects again to ensure the project was removed
    projects_list = database_api_client.list_projects()
    project_ids = [project.gcp_project_id for project in projects_list]
    assert project_data.gcp_project_id not in project_ids
