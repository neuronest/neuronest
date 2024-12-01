variable "image_name" {
  type = string
}
variable "service_account_name" {
  type = string
}
variable "models_bucket" {
  type = string
}
variable "samples_bucket" {
  type = string
}
variable "results_bucket" {
  type = string
}
variable "model_name" {
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
variable "cloud_run_env_vars" {
  type    = map(string)
  default = {}
}
variable "vpc_access_connector" {
  type = string
}
