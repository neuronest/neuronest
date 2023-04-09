resource "google_cloud_scheduler_job" "uninstantiate_job" {
  provider         = google-beta
  name             = var.cloud_cloud_scheduler_job_name
  schedule         = var.cloud_cloud_scheduler_schedule
  time_zone        = var.timezone

  http_target {
    http_method = "POST"
    uri         = var.cloud_cloud_scheduler_url
    body        = base64encode(var.cloud_cloud_scheduler_body)
  }
}
