# default dummy values when running focusing on the base module
variable "service_evaluator_image_name" {
  type    = string
  default = "service_evaluator_image_name_default"
}
variable "service_evaluator_serialized_service_client_parameters" {
  type    = string
  default = "service_evaluator_serialized_service_client_parameters_default"
}
variable "service_evaluator_service_name" {
  type    = string
  default = "service_evaluator_service_name_default"
}
variable "service_evaluator_webapp_service_account_name" {
  type = string
}
variable "service_evaluator_firestore_jobs_collection" {
  type = string
}
variable "service_evaluator_job_prefix_name" {
  type = string
}
variable "service_evaluator_cloud_run_name" {
  type = string
}
variable "service_evaluator_cloud_run_memory" {
  type = string
}
variable "service_evaluator_cloud_run_cpu" {
  type = string
}
variable "service_evaluator_cloud_run_min_scale" {
  type = string
}
variable "service_evaluator_cloud_run_max_scale" {
  type = string
}
