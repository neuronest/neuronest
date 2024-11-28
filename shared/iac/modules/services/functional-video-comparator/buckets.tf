#############################################
#    Google Storage Buckets    #
#############################################
resource "google_storage_bucket" "samples_bucket" {
  name          = var.video_comparator_samples_bucket
  project       = var.project_id
  force_destroy = true
  location      = var.region
  storage_class = "STANDARD"
  versioning {
    enabled = false
  }
}
resource "google_storage_bucket" "embeddings_bucket" {
  name          = var.video_comparator_embeddings_bucket
  project       = var.project_id
  force_destroy = true
  location      = var.region
  storage_class = "STANDARD"
  versioning {
    enabled = false
  }
}
resource "google_storage_bucket" "results_bucket" {
  name          = var.video_comparator_results_bucket
  project       = var.project_id
  force_destroy = true
  location      = var.region
  storage_class = "STANDARD"
  versioning {
    enabled = false
  }
}
