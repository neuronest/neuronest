variable "state_bucket" {
  type = string
}
variable "repository_name" {
  type = string
}
variable "image_name" {
  type = string
}
variable "webapp_service_account_name" {
  type = string
}
variable "cloud_scheduler_service_account_name" {
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
variable "cloud_scheduler_job_name" {
  type = string
}
variable "cloud_scheduler_schedule" {
  type = string
}
variable "cloud_uninstantiate_route" {
  type = string
}
variable "cloud_scheduler_model_name" {
  type    = string
  default = "cloud_scheduler_model_name_dummy"
}
