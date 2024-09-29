variable "online_prediction_model_service_account_name" {
  type = string
}
variable "online_prediction_model_models_bucket" {
  type = string
}
variable "online_prediction_model_model_name" {
  type = string
}
variable "online_prediction_model_cloud_run_name" {
  type = string
}
variable "online_prediction_model_cloud_run_memory" {
  type = string
}
variable "online_prediction_model_cloud_run_cpu" {
  type = string
}
variable "online_prediction_model_cloud_run_image_name" {
  type = string
}
variable "online_prediction_model_cloud_run_min_scale" {
  type = string
}
variable "online_prediction_model_cloud_run_max_scale" {
  type = string
}
variable "online_prediction_model_cloud_run_env_vars" {
  type    = map(string)
  default = {}
}
