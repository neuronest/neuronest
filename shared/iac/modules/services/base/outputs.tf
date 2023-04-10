output "infrastructure_builder_key" {
  value = google_service_account_key.infrastructure_builder_key.private_key
  sensitive = true
}