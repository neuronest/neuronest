# Create a service account
resource "google_service_account" "people_counting_api_sa" {
  provider     = google-beta
  account_id   = var.service_account_name
  display_name = "Webapp Service Account"
}
