##############################################
#       Deploy API to Google Cloud Run       #
##############################################
# Deploy image to Cloud Run
resource "google_cloud_run_service" "evaluator_api" {
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
        env {
          name  = "FIRESTORE_JOBS_COLLECTION"
          value = var.firestore_jobs_collection
        }
        env {
          name  = "JOB_PREFIX_NAME"
          value = var.job_prefix_name
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
          name  = "SERIALIZED_SERVICE_CLIENT_PARAMETERS"
          value = var.serialized_service_client_parameters
        }
        env {
          name  = "SERVICE_NAME"
          value = var.service_name
        }
      }
      service_account_name = google_service_account.evaluator_api_sa.email
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
    google_service_account.evaluator_api_sa
  ]
}
