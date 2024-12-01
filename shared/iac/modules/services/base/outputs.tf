output "project_builder_sa_key" {
  value = google_service_account_key.project_builder_sa_key.private_key
}
output "vpc_access_connector" {
  value = google_vpc_access_connector.serverless_connector.id
}
