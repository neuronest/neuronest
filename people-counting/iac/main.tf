terraform {
  required_providers {
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "4.25.0"
    }
  }
}
provider "google-beta" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

#############################################
#               Enable APIs                #
#############################################

# Enable IAM API
resource "google_project_service" "iam" {
  provider = google-beta
  service            = "iam.googleapis.com"
  disable_on_destroy = false
}
# Enable Artifact Registry API
resource "google_project_service" "artifact_registry" {
  provider = google-beta
  service            = "artifactregistry.googleapis.com"
  disable_on_destroy = false
}
# Enable Cloud Run API
resource "google_project_service" "cloud_run" {
  provider = google-beta
  service            = "run.googleapis.com"
  disable_on_destroy = false
}
# Enable Cloud Resource Manager API
resource "google_project_service" "resource_manager" {
  provider = google-beta
  service            = "cloudresourcemanager.googleapis.com"
  disable_on_destroy = false
}

# This is used so there is some time for the activation of the APIs to propagate through
# Google Cloud before actually calling them.
resource "time_sleep" "api_activation_waiting" {
  create_duration = "30s"
  depends_on = [
    google_project_service.iam,
    google_project_service.artifact_registry,
    google_project_service.cloud_run,
    google_project_service.resource_manager
    ]
}

#############################################
#    Google Artifact Registry Repository    #
#############################################
# Create Artifact Registry Repository for Docker containers
resource "google_artifact_registry_repository" "docker_repository" {
  provider = google-beta
  location = var.region
  repository_id = "${var.project_name}-arr"
  format = "DOCKER"
  depends_on = [time_sleep.api_activation_waiting]
}
# Create a service account
resource "google_service_account" "github_action" {
  provider = google-beta
  account_id   = "github-action"
  display_name = "GitHub Action CI Service Account"
  depends_on = [time_sleep.api_activation_waiting]
}
# Give service account permission to push to the Artifact Registry Repository
resource "google_artifact_registry_repository_iam_member" "github_action_iam" {
  provider = google-beta
  location = google_artifact_registry_repository.docker_repository.location
  repository =  google_artifact_registry_repository.docker_repository.repository_id
  role   = "roles/artifactregistry.writer"
  member = "serviceAccount:${google_service_account.github_action.email}"
  depends_on = [
    google_artifact_registry_repository.docker_repository,
    google_service_account.github_action
  ]
}

##############################################
#       Deploy API to Google Cloud Run       #
##############################################
# Deploy image to Cloud Run
resource "google_cloud_run_service" "cloud_run" {
  provider = google-beta
  name     = "${var.project_name}-cr-${var.stage}"
  location = var.region
  template {
    spec {
        containers {
            image = var.image_name
            resources {
                limits = {
                "memory" = var.cloud_run_memory
                "cpu" = var.cloud_run_cpu
                }
            }
        }
    }
    metadata {
        annotations = {
            "autoscaling.knative.dev/minScale" = var.cloud_run_min_scale
            "autoscaling.knative.dev/maxScale" = var.cloud_run_max_scale
        }
    }
  }
  traffic {
    percent = 100
    latest_revision = true
  }
  depends_on = [google_artifact_registry_repository_iam_member.github_action_iam]
}
