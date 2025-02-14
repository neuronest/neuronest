resource "google_cloud_run_v2_service" "people_counting_api" {
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
        name  = "COUNTED_VIDEOS_BUCKET"
        value = var.counted_videos_bucket
      }
      env {
        name  = "RESULTS_BUCKET"
        value = var.results_bucket
      }
      env {
        name  = "FIRESTORE_JOBS_COLLECTION"
        value = var.firestore_jobs_collection
      }
      env {
        name  = "SAMPLES_BUCKET"
        value = var.samples_bucket
      }
      env {
        name  = "OBJECT_DETECTION_HOST"
        value = var.object_detection_host
      }
    }
    scaling {
      min_instances = var.cloud_run_min_scale
      max_instances = var.cloud_run_max_scale
    }

    service_account = google_service_account.people_counting_api_sa.email
    timeout         = var.cloud_run_timeout
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
