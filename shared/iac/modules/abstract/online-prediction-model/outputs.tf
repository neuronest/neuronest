output "url" {
  value = google_cloud_run_service.web_serving.status[0].url
}
output "model_name" {
  value = var.model_name
}
output "service_account" {
  value = google_service_account.online_prediction_model_sa
}
