# SHARED VARIABLES
variable "project_id" {
  type = string
}
variable "region" {
  type = string
}
variable "zone" {
  type = string
}
variable "organization_id" {
  type = string
}
variable "billing_account" {
  type = string
}
variable "firestore_region" {
  type = string
}
variable "project_builder_service_account_name" {
  type = string
}
variable "mono_repository_name" {
  type = string
}
variable "timezone" {
  type = string
}
# END OF SHARED VARIABLES
# default dummy value when running focusing on the base module
variable "people_counting_image_name" {
  type = string
  default = "people_counting_image_name_dummy"
}
variable "people_counting_webapp_service_account_name" {
  type = string
}
variable "people_counting_firestore_results_collection" {
  type = string
}
variable "people_counting_videos_to_count_bucket" {
  type = string
}
variable "people_counting_counted_videos_bucket" {
  type = string
}
variable "people_counting_model_instantiator_host" {
  type = string
}
variable "people_counting_object_detection_model_name" {
  type = string
}
variable "people_counting_cloud_run_memory" {
  type = string
}
variable "people_counting_cloud_run_cpu" {
  type = string
}
variable "people_counting_cloud_run_min_scale" {
  type = string
}
variable "people_counting_cloud_run_max_scale" {
  type = string
}
variable "object_detection_repository_name" {
  type = string
}
variable "object_detection_service_account_name" {
  type = string
}
variable "object_detection_models_bucket" {
  type = string
}
variable "object_detection_package_name" {
  type = string
}
variable "model_instantiator_repository_name" {
  type = string
}
# default dummy value when running focusing on the base module
variable "model_instantiator_image_name" {
  type = string
  default = "model_instantiator_image_name_dummy"
}
variable "model_instantiator_webapp_service_account_name" {
  type = string
}
variable "model_instantiator_cloud_scheduler_service_account_name" {
  type = string
}
variable "model_instantiator_cloud_run_memory" {
  type = string
}
variable "model_instantiator_cloud_run_cpu" {
  type = string
}
variable "model_instantiator_cloud_run_min_scale" {
  type = string
}
variable "model_instantiator_cloud_run_max_scale" {
  type = string
}
variable "model_instantiator_cloud_scheduler_job_name" {
  type = string
}
variable "model_instantiator_cloud_scheduler_schedule" {
  type = string
}
variable "model_instantiator_cloud_uninstantiate_route" {
  type = string
}
