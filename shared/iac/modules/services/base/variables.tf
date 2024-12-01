variable "project_id" {
  type = string
}
variable "region" {
  type = string
}
variable "firestore_region" {
  type = string
}
variable "project_builder_service_account_name" {
  type = string
}
variable "mono_repository_name" {
  type = string
}
# VPC
variable "vpc_network" {
  type = string
}
variable "psa_range_name" {
  type = string
}
variable "serverless_connector_name" {
  type = string
}
variable "subnet_name" {
  type = string
}
variable "subnet_cidr_range" {
  type = string
}
variable "serverless_connector_cidr" {
  type = string
}
variable "psa_prefix_length" {
  type = string
}
variable "min_throughput" {
  type = string
}
variable "max_throughput" {
  type = string
}
