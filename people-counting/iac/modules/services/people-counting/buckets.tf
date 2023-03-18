#############################################
#    Google Storage Buckets    #
#############################################
resource "google_storage_bucket" "videos_to_count_bucket" {
  name          = var.videos_to_count_bucket
  project       = var.project_id
  force_destroy = true
  location      = var.region
  storage_class = "STANDARD"
  versioning {
    enabled = false
  }
  depends_on = [time_sleep.api_activation_waiting]
}
resource "google_storage_bucket" "counted_videos_bucket" {
  name          = var.counted_videos_bucket
  project       = var.project_id
  force_destroy = true
  location      = var.region
  storage_class = "STANDARD"
  versioning {
    enabled = false
  }
  depends_on = [time_sleep.api_activation_waiting]
}
