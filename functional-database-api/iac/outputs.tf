output "base_project_builder_sa_key" {
  value     = module.base.project_builder_sa_key
  sensitive = true
}
output "model_instantiator_url" {
  value = module.functional_database_api.model_instantiator_url
}
output "database_api_url" {
  value = module.functional_database_api.database_api_url
}
output "cloud_sql_instance_name" {
  value = module.functional_database_api.cloud_sql_instance_name
}
