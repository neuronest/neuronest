##############################################
#       Deploy API to Google Cloud Run       #
##############################################
# Deploy image to Cloud Run v2
resource "google_cloud_run_v2_service" "model_instantiator_api" {
  provider = google-beta
  name     = var.cloud_run_name
  location = var.region

  template {
    containers {
      image = var.image_name
      resources {
        limits {
          cpu    = var.cloud_run_cpu
          memory = var.cloud_run_memory
        }
      }
      env {
        name  = "PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "REGION"
        value = var.region
      }
      env {
        name  = "IMAGE_NAME"
        value = var.image_name
      }
      env {
        name  = "VERTEX_LOCATION"
        value = var.vertex_location
      }
    }
    scaling {
      min_instances = var.cloud_run_min_scale
      max_instances = var.cloud_run_max_scale
    }

    service_account = google_service_account.model_instantiator_api_sa.email
    timeout         = var.cloud_run_timeout
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  depends_on = [
    time_sleep.api_activation_waiting,
    google_service_account.model_instantiator_api_sa
  ]
}
