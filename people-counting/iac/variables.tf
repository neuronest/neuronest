variable "project_id" {
  type        = string
}
variable "project_name" {
  type        = string
}
variable "region" {
  type        = string
}
variable "zone" {
  type        = string
}
variable "stage" {
  type        = string
}
variable "image_name" {
  type        = string
}
variable "cloud_run_min_scale" {
  type        = string
  default     = "0"
}
variable "cloud_run_max_scale" {
  type        = string
  default     = "1"
}
variable "cloud_run_memory" {
  type        = string
  default     = "1G"
}
variable "cloud_run_cpu" {
  type        = string
  default     = "1"
}
