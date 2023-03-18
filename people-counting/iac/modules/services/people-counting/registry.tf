#############################################
#    Google Artifact Registry Repository    #
#############################################
#
# Create Artifact Registry Repository for Docker containers
resource "google_artifact_registry_repository" "people_counting_api_repository" {
  provider      = google-beta
  location      = var.region
  repository_id = var.repository_name
  format        = "DOCKER"
  depends_on    = [time_sleep.api_activation_waiting]
}
