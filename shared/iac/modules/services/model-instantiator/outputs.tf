output "url" {
  value = google_cloud_run_service.model_instantiator_api.status[0].url
}
