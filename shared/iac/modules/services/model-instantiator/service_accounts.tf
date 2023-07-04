resource "google_service_account" "model_instantiator_api_sa" {
  provider     = google-beta
  account_id   = var.webapp_service_account_name
  display_name = "Webapp Service Account"
}
resource "google_service_account" "model_instantiator_cloud_scheduler_sa" {
  provider     = google-beta
  account_id   = var.cloud_scheduler_service_account_name
  display_name = "Cloud Scheduler Service Account"
}
