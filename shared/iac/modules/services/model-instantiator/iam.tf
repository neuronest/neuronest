# Give model_instantiator_api service account permissions to act as
# online_prediction_model service account
resource "google_service_account_iam_binding" "model_instantiator_api_sa_act_as_online_prediction_model_sa" {
  service_account_id = var.online_prediction_model_sa_name
  role               = "roles/iam.serviceAccountUser"

  members = [
    "serviceAccount:${google_service_account.model_instantiator_api_sa.email}",
  ]
}
resource "google_project_iam_member" "model_instantiator_api_sa_aiplatform_admin" {
  project = var.project_id
  role    = "roles/aiplatform.admin"
  member  = "serviceAccount:${google_service_account.model_instantiator_api_sa.email}"
}
resource "google_project_iam_member" "model_instantiator_api_sa_datastore_owner" {
  project = var.project_id
  role    = "roles/datastore.owner"
  member  = "serviceAccount:${google_service_account.model_instantiator_api_sa.email}"
}
resource "google_project_iam_member" "model_instantiator_api_sa_service_account_user" {
  project = var.project_id
  role    = "roles/iam.serviceAccountUser"
  member  = "serviceAccount:${google_service_account.model_instantiator_api_sa.email}"
}
resource "google_project_iam_member" "model_instantiator_api_sa_logging_view_accessor" {
  project = var.project_id
  role    = "roles/logging.viewAccessor"
  member  = "serviceAccount:${google_service_account.model_instantiator_api_sa.email}"
}
resource "google_project_iam_member" "model_instantiator_api_sa_logging_viewer" {
  project = var.project_id
  role    = "roles/logging.viewer"
  member  = "serviceAccount:${google_service_account.model_instantiator_api_sa.email}"
}
resource "google_project_iam_member" "model_instantiator_api_sa_run_admin" {
  project = var.project_id
  role    = "roles/run.admin"
  member  = "serviceAccount:${google_service_account.model_instantiator_api_sa.email}"
}
resource "google_project_iam_member" "model_instantiator_cloud_scheduler_sa_run_invoker" {
  project = var.project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.model_instantiator_cloud_scheduler_sa.email}"
}
