output "base_project_builder_sa_key" {
  value     = module.base.project_builder_sa_key
  sensitive = true
}
output "model_instantiator_url" {
  value = module.database_api.model_instantiator_url
}
output "url" {
  value = module.database_api.url
}
output "cloud_sql_instance_name" {
  value = module.database_api.cloud_sql_instance_name
}
