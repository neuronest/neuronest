# Create a service account
resource "google_service_account" "model_instantiator_api_sa" {
  provider     = google-beta
  account_id   = "model-instantiator-api"
  display_name = "Webapp Service Account"
}
