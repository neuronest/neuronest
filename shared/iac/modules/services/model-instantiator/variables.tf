variable "image_name" {
  type = string
}
variable "webapp_service_account_name" {
  type = string
}
variable "cloud_scheduler_service_account_name" {
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
variable "cloud_scheduler_job_name" {
  type     = string
  nullable = true
  default  = null
}
variable "cloud_scheduler_schedule" {
  type     = string
  nullable = true
  default  = null
}
variable "cloud_scheduler_model_name" {
  type     = string
  nullable = true
  default  = null
}
variable "cloud_uninstantiate_route" {
  type     = string
  nullable = true
  default  = null
}
variable "cloud_scheduler_cloud_sql_instance_name" {
  type     = string
  nullable = true
  default  = null
}
variable "cloud_scheduler_cloud_sql_job_name" {
  type     = string
  nullable = true
  default  = null
}
variable "cloud_scheduler_cloud_sql_schedule" {
  type     = string
  nullable = true
  default  = null
}
variable "cloud_sql_uninstantiate_route" {
  type     = string
  nullable = true
  default  = null
}
variable "online_prediction_model_sa_name" {
  type     = string
  nullable = true
  default  = null
}
