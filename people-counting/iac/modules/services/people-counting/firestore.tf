
#############################################
#    Firestore    #
#############################################
# Create Firestore Database
resource "google_app_engine_application" "firestore_app" {
  project       = var.project_id
  location_id   = var.region
  database_type = "CLOUD_FIRESTORE"
  depends_on    = [time_sleep.api_activation_waiting]
}
