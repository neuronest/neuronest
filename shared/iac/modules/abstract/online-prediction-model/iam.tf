resource "google_project_iam_member" "online_prediction_model_aiplatform_admin" {
  project = var.project_id
  role    = "roles/aiplatform.admin"
  member  = "serviceAccount:${google_service_account.online_prediction_model_sa.email}"
}
resource "google_project_iam_member" "online_prediction_model_artifact_registry_reader" {
  project = var.project_id
  role    = "roles/artifactregistry.reader"
  member  = "serviceAccount:${google_service_account.online_prediction_model_sa.email}"
}
resource "google_project_iam_member" "online_prediction_model_bigquery_admin" {
  project = var.project_id
  role    = "roles/bigquery.admin"
  member  = "serviceAccount:${google_service_account.online_prediction_model_sa.email}"
}
resource "google_project_iam_member" "online_prediction_model_storage_admin" {
  project = var.project_id
  role    = "roles/storage.admin"
  member  = "serviceAccount:${google_service_account.online_prediction_model_sa.email}"
}
resource "google_project_iam_member" "online_prediction_model_storage_object_admin" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.online_prediction_model_sa.email}"
}
