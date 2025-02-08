##############################################
#       Deploy API to Google Cloud Run       #
##############################################
resource "google_cloud_run_service" "web_serving" {
  provider                   = google-beta
  name                       = var.cloud_run_name
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
        dynamic "env" {
          for_each = var.cloud_run_env_vars

          content {
            name  = env.key
            value = env.value
          }
        }
      }
      service_account_name = google_service_account.online_prediction_model_sa.email
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
    google_service_account.online_prediction_model_sa,
  ]
}
