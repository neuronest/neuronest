# Create a service account
resource "google_service_account" "object_detection_sa" {
  provider     = google-beta
  account_id   = "object-detection"
  display_name = "Object detection service account"
  depends_on   = [time_sleep.api_activation_waiting]
}
