resource "google_service_account" "model_instantiator_api_sa" {
  provider     = google-beta
  account_id   = "model-instantiator-api"
  display_name = "Webapp Service Account"
}
resource "google_service_account" "model_instantiator_cloud_scheduler_sa" {
  provider     = google-beta
  account_id   = "cloud-scheduler-uninstantiate"
  display_name = "Cloud Scheduler Service Account"
}
