##############################################
#       Deploy API to Google Cloud Run       #
##############################################
# Deploy image to Cloud Run
resource "google_cloud_run_service" "model-instantiator_api" {
  provider                   = google-beta
  name                       = var.project_name
  location                   = var.region
  autogenerate_revision_name = true
  template {
    spec {
      containers {
        image = var.image_name
        resources {
          limits = {
            "memory" = var.cloud_run_memory
            "cpu"    = var.cloud_run_cpu
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
      }
      service_account_name = google_service_account.model_instantiator_api_sa.email
    }
    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale" = var.cloud_run_min_scale
        "autoscaling.knative.dev/maxScale" = var.cloud_run_max_scale
      }
    }
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
