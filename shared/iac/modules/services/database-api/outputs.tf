output "url" {
  value = google_cloud_run_service.database_api.status[0].url
}
output "cloud_sql_instance_name" {
  value = google_sql_database_instance.neuronest_instance.name
}
output "model_instantiator_url" {
  value = module.model_instantiator.url
}

