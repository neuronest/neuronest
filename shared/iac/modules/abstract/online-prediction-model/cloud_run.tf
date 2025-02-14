##############################################
#  Deploy API to Google Cloud Run (v2)       #
##############################################
resource "google_cloud_run_v2_service" "web_serving" {
  name     = var.cloud_run_name
  location = var.region

  template {
    containers {
      image = var.image_name
      resources {
        limits {
          memory = var.cloud_run_memory
          cpu    = var.cloud_run_cpu
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
    scaling {
      min_instances = var.cloud_run_min_scale
      max_instances = var.cloud_run_max_scale
    }

    service_account = google_service_account.online_prediction_model_sa.email
    timeout         = var.cloud_run_timeout
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
