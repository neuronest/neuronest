resource "google_project_iam_member" "infrastructure_builder_sa_owner" {
  project = var.project_id
  role    = "roles/owner"
  member  = "serviceAccount:${google_service_account.infrastructure_builder_sa.email}"
}