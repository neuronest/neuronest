from core.client.database_api import DatabaseApiClient


# pylint: disable=unused-argument
def test_create_project(
    database_api_client: DatabaseApiClient,
    uninstantiate_teardown,
):
    project_data = {"gcp_project_id": "dummy-test-created-gcp-project"}

    # Make the POST request to create the project
    created_project = database_api_client.create_project(
        gcp_project_id=project_data["gcp_project_id"]
    )

    assert created_project == project_data["gcp_project_id"]
