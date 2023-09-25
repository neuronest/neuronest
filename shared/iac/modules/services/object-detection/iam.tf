resource "google_project_iam_member" "object_detection_aiplatform_admin" {
  project = var.project_id
  role    = "roles/aiplatform.admin"
  member  = "serviceAccount:${google_service_account.object_detection_sa.email}"
}
resource "google_project_iam_member" "object_detection_artifact_registry_reader" {
  project = var.project_id
  role    = "roles/artifactregistry.reader"
  member  = "serviceAccount:${google_service_account.object_detection_sa.email}"
}
resource "google_project_iam_member" "object_detection_bigquery_admin" {
  project = var.project_id
  role    = "roles/bigquery.admin"
  member  = "serviceAccount:${google_service_account.object_detection_sa.email}"
}
resource "google_project_iam_member" "object_detection_storage_admin" {
  project = var.project_id
  role    = "roles/storage.admin"
  member  = "serviceAccount:${google_service_account.object_detection_sa.email}"
}
resource "google_project_iam_member" "object_detection_storage_object_admin" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.object_detection_sa.email}"
}
