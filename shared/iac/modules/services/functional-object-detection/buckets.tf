#############################################
#    Google Storage Buckets    #
#############################################
resource "google_storage_bucket" "samples_bucket" {
  name          = var.object_detection_samples_bucket
  project       = var.project_id
  force_destroy = true
  location      = var.region
  storage_class = "STANDARD"
  versioning {
    enabled = false
  }
}
resource "google_storage_bucket" "results_bucket" {
  name          = var.object_detection_results_bucket
  project       = var.project_id
  force_destroy = true
  location      = var.region
  storage_class = "STANDARD"
  versioning {
    enabled = false
  }
}
