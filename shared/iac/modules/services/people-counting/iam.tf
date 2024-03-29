resource "google_project_iam_member" "people_counting_api_sa_uses_firestore" {
  project = var.project_id
  role    = "roles/datastore.owner"
  member  = "serviceAccount:${google_service_account.people_counting_api_sa.email}"
}
resource "google_project_iam_member" "people_counting_api_sa_is_storage_admin" {
  project = var.project_id
  role    = "roles/storage.admin"
  member  = "serviceAccount:${google_service_account.people_counting_api_sa.email}"
}
resource "google_project_iam_member" "people_counting_api_sa_is_aiplatform_admin" {
  project = var.project_id
  role    = "roles/aiplatform.admin"
  member  = "serviceAccount:${google_service_account.people_counting_api_sa.email}"
}
resource "google_project_iam_member" "people_counting_api_sa_is_service_account_user" {
  project = var.project_id
  role    = "roles/iam.serviceAccountUser"
  member  = "serviceAccount:${google_service_account.people_counting_api_sa.email}"
}
resource "google_project_iam_member" "people_counting_api_sa_is_cloud_run_admin" {
  project = var.project_id
  role    = "roles/run.admin"
  member  = "serviceAccount:${google_service_account.people_counting_api_sa.email}"
}
resource "google_project_iam_member" "people_counting_api_sa_is_cloud_run_invoker" {
  project = var.project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.people_counting_api_sa.email}"
}
