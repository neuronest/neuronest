output "base_project_builder_sa_key" {
  value     = module.base.project_builder_sa_key
  sensitive = true
}
output "base_vpc_access_connector" {
  value = module.base.vpc_access_connector
}
output "model_instantiator_url" {
  value = module.functional_video_comparator.model_instantiator_url
}
output "online_prediction_model_url" {
  value = module.functional_video_comparator.online_prediction_model_url
}
