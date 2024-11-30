#############################################
#    Google Storage Buckets    #
#############################################
resource "google_storage_bucket" "models_bucket" {
  name          = var.models_bucket
  project       = var.project_id
  force_destroy = true
  location      = var.region
  storage_class = "STANDARD"
  versioning {
    enabled = false
  }
  depends_on = [time_sleep.api_activation_waiting]
}
resource "google_storage_bucket" "samples_bucket" {
  name          = var.samples_bucket
  project       = var.project_id
  force_destroy = true
  location      = var.region
  storage_class = "STANDARD"
  versioning {
    enabled = false
  }
  depends_on = [time_sleep.api_activation_waiting]
}
resource "google_storage_bucket" "results_bucket" {
  name          = var.results_bucket
  project       = var.project_id
  force_destroy = true
  location      = var.region
  storage_class = "STANDARD"
  versioning {
    enabled = false
  }
  depends_on = [time_sleep.api_activation_waiting]
}
