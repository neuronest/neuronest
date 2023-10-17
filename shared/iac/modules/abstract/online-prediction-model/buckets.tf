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
