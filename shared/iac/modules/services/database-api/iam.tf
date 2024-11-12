resource "google_project_iam_member" "database_api_sa_run_admin" {
  project = var.project_id
  role    = "roles/run.admin"
  member  = "serviceAccount:${google_service_account.database_api_sa.email}"
}
resource "google_project_iam_member" "database_api_sa_cloudsql_admin" {
  project = var.project_id
  role    = "roles/cloudsql.admin"
  member  = "serviceAccount:${google_service_account.database_api_sa.email}"
}
