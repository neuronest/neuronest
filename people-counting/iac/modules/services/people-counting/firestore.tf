
#############################################
#    Firestore    #
#############################################
# Create Firestore Database
resource "google_app_engine_application" "firestore_app" {
  project     = var.project_id
  location_id = var.location_app_engine
  database_type = "CLOUD_FIRESTORE"
}