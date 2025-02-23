output "model_instantiator_url" {
  value = module.object_detection.model_instantiator_url
}
output "url" {
  value = google_cloud_run_v2_service.people_counting_api.uri
}
