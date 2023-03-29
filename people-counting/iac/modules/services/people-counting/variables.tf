variable "project_id" {
  type = string
}
variable "project_name" {
  type = string
}
variable "region" {
  type = string
}
variable "firestore_region" {
  type = string
}
variable "repository_name" {
  type = string
}
variable "webapp_image" {
  type = string
}
variable "firestore_results_collection" {
  type = string
}
variable "videos_to_count_bucket" {
  type = string
}
variable "counted_videos_bucket" {
  type = string
}
variable "model_instantiator_host" {
  type = string
}
variable "object_detection_model_name" {
  type = string
}
variable "cloud_run_memory" {
  type = string
}
variable "cloud_run_cpu" {
  type = string
}
variable "cloud_run_min_scale" {
  type = string
}
variable "cloud_run_max_scale" {
  type = string
}
variable "firestore_app_engine_location_id" {
  type = string
}
variable "set_up_cloud_run" {
  type = bool
}
