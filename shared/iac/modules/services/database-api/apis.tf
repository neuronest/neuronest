##############################################
##               Enable APIs                #
##############################################

# Enable Cloud Run API
resource "google_project_service" "cloud_run" {
  provider           = google-beta
  service            = "run.googleapis.com"
  disable_on_destroy = false
}

# Enable Cloud SQL Admin API
resource "google_project_service" "cloud_sql" {
  project = var.project_id
  service = "sqladmin.googleapis.com"
}

# This is used so there is some time for the activation of the APIs to propagate through
# Google Cloud before actually calling them.
resource "time_sleep" "api_activation_waiting" {
  create_duration = "30s"
  depends_on = [
    google_project_service.cloud_run,
    google_project_service.cloud_sql
  ]
}
