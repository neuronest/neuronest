variable "image_name" {
  type = string
}
variable "service_account_name" {
  type = string
}
variable "firestore_results_collection" {
  type = string
}
variable "firestore_jobs_collection" {
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
variable "cloud_run_name" {
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