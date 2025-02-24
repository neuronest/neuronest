output "model_instantiator_url" {
  value = module.model_instantiator.url
}
output "online_prediction_model_url" {
  value = google_cloud_run_v2_service.web_serving.uri
}
output "model_name" {
  value = var.model_name
}
output "service_account" {
  value = google_service_account.online_prediction_model_sa
}
