output "url" {
  value = google_cloud_run_service.people_counting_api.status[0].url
}
