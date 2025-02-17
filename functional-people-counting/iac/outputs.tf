output "base_project_builder_sa_key" {
  value     = module.base.project_builder_sa_key
  sensitive = true
}
output "people_counting_url" {
  value = module.functional_people_counting.people_counting_url
}
output "model_instantiator_url" {
  value = module.functional_people_counting.model_instantiator_url
}
output "service_evaluator_url" {
  value = module.functional_people_counting.service_evaluator_url
}
