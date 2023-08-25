output "model_name" {
  value = var.model_name
}
output "service_account_name" {
  value = google_service_account.online_prediction_model_sa.name
}
