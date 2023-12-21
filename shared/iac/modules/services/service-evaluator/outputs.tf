output "url" {
  value = google_cloud_run_service.evaluator_api.status[0].url
}
