output "base_project_builder_sa_key" {
  value     = module.base.project_builder_sa_key
  sensitive = true
}
output "model_instantiator_url" {
  value = module.functional_video_comparator.model_instantiator_url
}
output "online_prediction_model_url" {
  value = module.functional_video_comparator.online_prediction_model_url
}
