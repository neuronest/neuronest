resource "google_service_account" "project_builder_sa" {
  account_id   = var.project_builder_service_account_name
  display_name = var.project_builder_service_account_name
}
resource "google_service_account_key" "project_builder_sa_key" {
  service_account_id = google_service_account.project_builder_sa.id
}
