#############################################
#    Google Storage Buckets    #
#############################################
resource "google_storage_bucket" "videos_to_compare_bucket" {
  name          = var.videos_to_compare_bucket
  project       = var.project_id
  force_destroy = true
  location      = var.region
  storage_class = "STANDARD"
  versioning {
    enabled = false
  }
}
resource "google_storage_bucket" "embeddings_bucket" {
  name          = var.embeddings_bucket
  project       = var.project_id
  force_destroy = true
  location      = var.region
  storage_class = "STANDARD"
  versioning {
    enabled = false
  }
}
resource "google_storage_bucket" "job_results_bucket" {
  name          = var.job_results_bucket
  project       = var.project_id
  force_destroy = true
  location      = var.region
  storage_class = "STANDARD"
  versioning {
    enabled = false
  }
}
