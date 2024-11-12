resource "google_service_account" "database_api_sa" {
  provider     = google-beta
  account_id   = var.cloud_run_service_account_name
  display_name = "Webapp Service Account"
}
