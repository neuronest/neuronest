resource "google_service_account" "evaluator_api_sa" {
  provider     = google-beta
  account_id   = var.webapp_service_account_name
  display_name = "Webapp Service Account"
}
