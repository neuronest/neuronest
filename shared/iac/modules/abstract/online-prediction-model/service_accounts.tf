# Create a service account
resource "google_service_account" "online_prediction_model_sa" {
  provider     = google-beta
  account_id   = var.service_account_name
  display_name = "Online prediction model service account"
  depends_on   = [time_sleep.api_activation_waiting]
}
