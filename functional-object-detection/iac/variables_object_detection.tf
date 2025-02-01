variable "object_detection_image_name" {
  type    = string
  default = null
}
variable "object_detection_service_account_name" {
  type = string
}
variable "object_detection_models_bucket" {
  type = string
}
variable "object_detection_samples_bucket" {
  type = string
}
variable "object_detection_results_bucket" {
  type = string
}
variable "object_detection_model_name" {
  type = string
}
variable "object_detection_vertex_location" {
  type = string
}
variable "object_detection_cloud_run_name" {
  type = string
}
variable "object_detection_cloud_run_memory" {
  type = string
}
variable "object_detection_cloud_run_cpu" {
  type = string
}
variable "object_detection_cloud_run_min_scale" {
  type = string
}
variable "object_detection_cloud_run_max_scale" {
  type = string
}
variable "object_detection_firestore_jobs_collection" {
  type = string
}
