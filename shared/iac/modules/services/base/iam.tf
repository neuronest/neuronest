resource "google_project_iam_member" "project_builder_sa_project_owner" {
  project = var.project_id
  role    = "roles/owner"
  member  = "serviceAccount:${google_service_account.project_builder_sa.email}"
}