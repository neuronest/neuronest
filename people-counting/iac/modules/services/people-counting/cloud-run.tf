##############################################
#       Deploy API to Google Cloud Run       #
##############################################
# Deploy image to Cloud Run
resource "google_cloud_run_service" "people_counting_api" {
  provider = google-beta
  name     = var.project_name
  location = var.region
  autogenerate_revision_name = true
  template {
    spec {
      containers {
        image = var.webapp_image
        resources {
          limits = {
            "memory" = "4G"
            "cpu"    = "1"
          }
        }
        env {
          name = "COUNTED_VIDEOS_BUCKET"
          value = var.counted_videos_bucket
        }
        env {
          name = "FIRESTORE_RESULTS_COLLECTION"
          value = var.firestore_results_collection
        }
        env {
          name = "PROJECT_ID"
          value = var.project_id
        }
        env {
          name = "VIDEOS_TO_COUNT_BUCKET"
          value = var.videos_to_count_bucket
        }
      }
      service_account_name = google_service_account.people_counting_api_sa.email
    }
    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale" = "0"
        "autoscaling.knative.dev/maxScale" = "1"
      }
    }
  }
  traffic {
      percent         = 100
      latest_revision = true
    }
  depends_on = [
    google_service_account.people_counting_api_sa
    # google_service_account_iam_member.ci-sa-uses-api-sa
  ]
}
data "google_iam_policy" "no_auth_cloud_run" {
  binding {
    role = "roles/run.invoker"
    members = [
      "allUsers",
    ]
  }
}
resource "google_cloud_run_service_iam_policy" "no_auth_people_counting_api" {
  location    = google_cloud_run_service.people_counting_api.location
  project     = google_cloud_run_service.people_counting_api.project
  service     = google_cloud_run_service.people_counting_api.name

  policy_data = data.google_iam_policy.no_auth_cloud_run.policy_data
}