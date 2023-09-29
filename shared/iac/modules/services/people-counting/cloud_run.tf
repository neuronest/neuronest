##############################################
#       Deploy API to Google Cloud Run       #
##############################################
# Deploy image to Cloud Run
resource "google_cloud_run_service" "people_counting_api" {
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
          name  = "COUNTED_VIDEOS_BUCKET"
          value = var.counted_videos_bucket
        }
        env {
          name  = "FIRESTORE_RESULTS_COLLECTION"
          value = var.firestore_results_collection
        }
        env {
          name  = "OBJECT_DETECTION_MODEL_NAME"
          value = var.object_detection_model_name
        }
        env {
          name  = "MODEL_INSTANTIATOR_HOST"
          value = var.model_instantiator_host
        }
        env {
          name  = "VIDEOS_TO_COUNT_BUCKET"
          value = var.videos_to_count_bucket
        }
      }
      service_account_name = google_service_account.people_counting_api_sa.email
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
    google_service_account.people_counting_api_sa
  ]
}
