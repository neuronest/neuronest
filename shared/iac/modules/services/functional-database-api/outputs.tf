#output "model_instantiator_url" {
#  value = module.functional_object_detection.model_instantiator_url
#}
#output "cloud_sql_name" {
#  value = module.cloud_sql.name
#}
output "model_instantiator_url" {
  value = module.model_instantiator.url
}
output "database_api_url" {
  value = module.database_api.url
}
output "cloud_sql_instance_name" {
  value = module.database_api.cloud_sql_instance_name
}
