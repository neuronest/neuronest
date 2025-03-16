variable "image_name" {
  type    = string
  default = "image_name_dummy"
}
variable "cloud_sql_instance_name" {
  type = string
}
variable "cloud_sql_db_name" {
  type = string
}
variable "cloud_sql_enable_automatic_storage_increases" {
  type = bool
}
variable "cloud_sql_enable_public_ip" {
  type = bool
}
variable "cloud_sql_disk_type" {
  type = string
}
variable "cloud_sql_database_version" {
  type = string
}
variable "cloud_sql_tier" {
  type = string
}
variable "cloud_run_cloud_sql_username" {
  type = string
}
variable "cloud_run_service_account_name" {
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
