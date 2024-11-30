##############################################
#       Deploy API to Google Cloud Run       #
##############################################

resource "google_compute_global_address" "private_access_range" {
  name          = "psa-range"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 24
  network       = var.vpc_network
  description   = "Reserved range for Private Service Access"
}
resource "google_service_networking_connection" "private_service_access" {
  network = var.vpc_network
  service = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [
    google_compute_global_address.private_access_range.name
  ]
}
resource "google_vpc_access_connector" "serverless_connector" {
  name    = "my-serverless-connector"
  region  = var.region
  network = var.vpc_network

  ip_cidr_range = "10.8.0.0/28"
}

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
        "autoscaling.knative.dev/minScale"        = var.cloud_run_min_scale
        "autoscaling.knative.dev/maxScale"        = var.cloud_run_max_scale
        "run.googleapis.com/vpc-access-connector" = google_vpc_access_connector.serverless_connector.id
        "run.googleapis.com/vpc-access-egress"    = "private-ranges-only"
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
    google_service_networking_connection.private_service_access,
    google_vpc_access_connector.serverless_connector
  ]
}
