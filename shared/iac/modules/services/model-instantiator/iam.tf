resource "google_project_iam_member" "model-instantiator-api-sa-aiplatform-admin" {
  project = var.project_id
  role    = "roles/aiplatform.admin"
  member  = "serviceAccount:${google_service_account.model_instantiator_api_sa.email}"
}
resource "google_project_iam_member" "model-instantiator-api-sa-datastore-owner" {
  project = var.project_id
  role    = "roles/datastore.owner"
  member  = "serviceAccount:${google_service_account.model_instantiator_api_sa.email}"
}
resource "google_project_iam_member" "model-instantiator-api-sa-service-account-user" {
  project = var.project_id
  role    = "roles/iam.serviceAccountUser"
  member  = "serviceAccount:${google_service_account.model_instantiator_api_sa.email}"
}
resource "google_project_iam_member" "model-instantiator-api-sa-logging-view-accessor" {
  project = var.project_id
  role    = "roles/logging.viewAccessor"
  member  = "serviceAccount:${google_service_account.model_instantiator_api_sa.email}"
}
resource "google_project_iam_member" "model-instantiator-api-sa-logging-viewer" {
  project = var.project_id
  role    = "roles/logging.viewer"
  member  = "serviceAccount:${google_service_account.model_instantiator_api_sa.email}"
}
resource "google_project_iam_member" "model-instantiator-api-sa-run-admin" {
  project = var.project_id
  role    = "roles/run.admin"
  member  = "serviceAccount:${google_service_account.model_instantiator_api_sa.email}"
}

resource "google_project_iam_member" "model-instantiator-cloud-scheduler-sa-run-invoker" {
  project = var.project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.model_instantiator_cloud_scheduler_sa.email}"
}
