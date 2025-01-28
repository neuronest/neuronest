##############################################
#       Deploy API to Google Cloud Run       #
##############################################
# Deploy image to Cloud Run
# Cloud Run Service with DB password as environment variable

# Retrieve the secret version to pass as an environment variable in Cloud Run
data "google_secret_manager_secret_version" "database_api_neuronest_instance_user_data" {
  secret  = google_secret_manager_secret.database_api_db_password_secret.name
  version = "latest"
}


resource "google_cloud_run_service" "database_api" {
  provider                   = google-beta
  name                       = var.cloud_run_name
  location                   = var.region
  autogenerate_revision_name = true
  template {
    spec {
      containers {
        image = var.image_name
        # Allows up to failure_threshold * period_seconds for the app to start
        # Ensures sufficient time for database migrations to complete
        startup_probe {
          initial_delay_seconds = 10 # Delay before the first check
          timeout_seconds       = 1  # Max time to wait for each check
          period_seconds        = 10 # Interval between checks
          failure_threshold     = 12 # Number of failed attempts before restart
        }


        resources {
          limits = {
            "memory" = var.cloud_run_memory
            "cpu"    = var.cloud_run_cpu
          }
        }
        env {
          name  = "DB_USER"
          value = var.cloud_run_cloud_sql_username
        }
        env {
          name  = "DB_PASSWORD"
          value = data.google_secret_manager_secret_version.database_api_neuronest_instance_user_data.secret_data
        }

        env {
          name  = "DB_NAME"
          value = google_sql_database.neuronest_database.name
        }
        env {
          name  = "CLOUD_SQL_CONNECTION_NAME"
          value = google_sql_database_instance.neuronest_instance.connection_name
        }
        env {
          name  = "INSTANCE_NAME"
          value = google_sql_database_instance.neuronest_instance.name
        }
        env {
          name  = "MODEL_INSTANTIATOR_HOST"
          value = var.model_instantiator_host
        }
      }
      service_account_name = google_service_account.database_api_sa.email
    }
    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale"      = var.cloud_run_min_scale
        "autoscaling.knative.dev/maxScale"      = var.cloud_run_max_scale
        "run.googleapis.com/cloudsql-instances" = "${var.project_id}:${var.region}:${google_sql_database_instance.neuronest_instance.name}"
      }
    }
  }
  traffic {
    percent         = 100
    latest_revision = true
  }
  depends_on = [
    google_service_account.database_api_sa,
    google_sql_database_instance.neuronest_instance,
    google_sql_database.neuronest_database,
    google_sql_user.database_api_neuronest_instance_user,
    google_secret_manager_secret_version.database_api_db_password_version
  ]

}