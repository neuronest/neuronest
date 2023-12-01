variable "people_counting_repository_name" {
  type = string
}
# default dummy value when running focusing on the base module
variable "people_counting_image_name" {
  type    = string
  default = "people_counting_image_name_default"
}
variable "people_counting_service_account_name" {
  type = string
}
variable "people_counting_firestore_results_collection" {
  type = string
}
variable "people_counting_firestore_jobs_collection" {
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
variable "people_counting_cloud_run_name" {
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
