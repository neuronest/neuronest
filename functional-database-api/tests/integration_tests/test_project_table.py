import requests
from core.client.database_api import DatabaseApiClient

# # pylint: disable=unused-argument
# def test_create_project(
#     database_api_client: DatabaseApiClient,
#     uninstantiate_teardown,
# ):
#     project_data = {"gcp_project_id": "dummy-test-created-gcp-project"}
#
#     # Make the POST request to create the project
#     created_project = database_api_client.create_project(
#         gcp_project_id=project_data["gcp_project_id"]
#     )
#     assert created_project.json()["gcp_project_id"] == project_data["gcp_project_id"]


# pylint: disable=unused-argument
def test_create_get_and_delete_project(
    database_api_client: DatabaseApiClient,
    uninstantiate_teardown,
):

    project_data = {"gcp_project_id": "dummy-test-create-delete"}

    # Step 1: Create the project
    created_project = database_api_client.create_project(
        gcp_project_id=project_data["gcp_project_id"]
    )
    assert created_project.json()["gcp_project_id"] == project_data["gcp_project_id"]

    # Step 2: Verify the project exists
    fetched_project = database_api_client.get_project(project_data["gcp_project_id"])
    assert fetched_project.status_code == 200
    assert fetched_project.json()["gcp_project_id"] == project_data["gcp_project_id"]

    # Step 3: Delete the project
    database_api_client.delete_project(gcp_project_id=project_data["gcp_project_id"])
    try:
        # Attempt to get the project; expect a 404
        database_api_client.get_project(project_data["gcp_project_id"])
    except requests.exceptions.HTTPError as http_error:
        if http_error.response.status_code == 404:
            # Normal scenario: 404 indicates the project does not exist
            pass
        else:
            # Re-raise for any other HTTP errors
            raise
