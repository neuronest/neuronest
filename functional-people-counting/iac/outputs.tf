output "base_project_builder_sa_key" {
  value     = module.base.project_builder_sa_key
  sensitive = true
}
output "object_detection_model_instantiator_url" {
  value = module.people_counting_functional.object_detection_model_instantiator_url
}
output "people_counting_url" {
  value = module.people_counting_functional.people_counting_url
}
