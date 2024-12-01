resource "google_compute_network" "private_endpoint_vpc" {
  project                 = var.project_id
  name                    = var.vpc_network
  auto_create_subnetworks = false
}
resource "google_compute_subnetwork" "private_endpoint_subnet" {
  project       = var.project_id
  name          = var.subnet_name
  ip_cidr_range = var.subnet_cidr_range
  region        = var.region
  network       = google_compute_network.private_endpoint_vpc.self_link
}
resource "google_compute_global_address" "private_access_range" {
  project       = var.project_id
  name          = var.psa_range_name
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = var.psa_prefix_length
  network       = google_compute_network.private_endpoint_vpc.self_link
}
resource "google_service_networking_connection" "private_service_access" {
  network = google_compute_network.private_endpoint_vpc.self_link
  service = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [
    google_compute_global_address.private_access_range.name
  ]
  depends_on = [
    google_project_service.enable_apis["servicenetworking.googleapis.com"],
    time_sleep.api_activation_waiting
  ]
}
resource "google_vpc_access_connector" "serverless_connector" {
  project        = var.project_id
  name           = var.serverless_connector_name
  region         = var.region
  network        = google_compute_network.private_endpoint_vpc.self_link
  ip_cidr_range  = var.serverless_connector_cidr
  min_throughput = var.min_throughput
  max_throughput = var.max_throughput
  depends_on = [
    time_sleep.api_activation_waiting
  ]
}
