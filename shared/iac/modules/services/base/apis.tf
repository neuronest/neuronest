
##############################################
##               Enable APIs                #
##############################################

# Enable IAM API
resource "google_project_service" "cloud_billing" {
  provider           = google-beta
  service            = "cloudbilling.googleapis.com"
  disable_on_destroy = false
}
# Enable IAM API
resource "google_project_service" "iam" {
  provider           = google-beta
  service            = "iam.googleapis.com"
  disable_on_destroy = false
}
# Enable Artifact Registry API
resource "google_project_service" "artifact_registry" {
  provider           = google-beta
  service            = "artifactregistry.googleapis.com"
  disable_on_destroy = false
}
# Enable Cloud Resource Manager API
resource "google_project_service" "resource_manager" {
  provider           = google-beta
  service            = "cloudresourcemanager.googleapis.com"
  disable_on_destroy = false
}
# Enable Firestore API
resource "google_project_service" "firestore" {
  provider           = google-beta
  service            = "firestore.googleapis.com"
  disable_on_destroy = false
}
# Enable App Engine API
resource "google_project_service" "appengine" {
  provider           = google-beta
  service            = "appengine.googleapis.com"
  disable_on_destroy = false
}

# This is used so there is some time for the activation of the APIs to propagate through
# Google Cloud before actually calling them.
resource "time_sleep" "api_activation_waiting" {
  create_duration = "90s"
  depends_on = [
    google_project_service.iam,
    google_project_service.artifact_registry,
    google_project_service.resource_manager,
    google_project_service.resource_manager,
    google_project_service.cloud_billing,
    google_project_service.firestore,
    google_project_service.appengine
  ]
}
