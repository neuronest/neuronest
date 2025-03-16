##############################################
##               Enable APIs                ##
##############################################

# Enable Cloud Run API
resource "google_project_service" "cloud_run" {
  provider           = google-beta
  project            = var.project_id
  service            = "run.googleapis.com"
  disable_on_destroy = false
}

# Enable Cloud SQL Admin API
resource "google_project_service" "cloud_sql" {
  project            = var.project_id
  service            = "sqladmin.googleapis.com"
  disable_on_destroy = false
}

# Enable Service Networking API
resource "google_project_service" "service_networking" {
  project            = var.project_id
  service            = "servicenetworking.googleapis.com"
  disable_on_destroy = false
}

# Enable Secret Manager API
resource "google_project_service" "secret_manager" {
  project            = var.project_id
  service            = "secretmanager.googleapis.com"
  disable_on_destroy = false
}

# Enable Compute Engine API
resource "google_project_service" "compute_engine" {
  project            = var.project_id
  service            = "compute.googleapis.com"
  disable_on_destroy = false
}

# This is used so there is some time for the activation of the APIs to propagate through
# Google Cloud before actually calling them.
resource "time_sleep" "api_activation_waiting" {
  create_duration = "30s"
  depends_on = [
    google_project_service.cloud_run,
    google_project_service.cloud_sql,
    google_project_service.secret_manager,
    google_project_service.service_networking,
    google_project_service.compute_engine
  ]
}

