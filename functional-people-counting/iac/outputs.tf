output "base_project_builder_sa_key" {
  value     = module.base.project_builder_sa_key
  sensitive = true
}
output "base_vpc_access_connector" {
  value = module.base.vpc_access_connector
}
output "people_counting_url" {
  value = module.functional_people_counting.people_counting_url
}
output "model_instantiator_url" {
  value = module.functional_people_counting.model_instantiator_url
}
