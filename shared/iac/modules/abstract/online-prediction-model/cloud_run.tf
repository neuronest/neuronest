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
        limits = {
          "cpu"    = var.cloud_run_cpu
          "memory" = var.cloud_run_memory
        }
        cpu_idle = true # Ensures CPU is allocated only during request processing
      }
      dynamic "env" {
        for_each = var.cloud_run_env_vars

        content {
          name  = env.key
          value = env.value
        }
      }
      env {
        name  = "MODEL_INSTANTIATOR_HOST"
        value = module.model_instantiator.url
      }

    }
    scaling {
      min_instance_count = var.cloud_run_min_scale
      max_instance_count = var.cloud_run_max_scale
    }

    service_account = google_service_account.online_prediction_model_sa.email
    timeout         = var.cloud_run_timeout
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  depends_on = [
    time_sleep.api_activation_waiting,
    google_service_account.online_prediction_model_sa,
  ]
}
