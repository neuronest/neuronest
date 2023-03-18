# Create a service account
resource "google_service_account" "people_counting_api_sa" {
  provider     = google-beta
  account_id   = "people-counting-api"
  display_name = "Webapp Service Account"
  depends_on   = [time_sleep.api_activation_waiting]
}
