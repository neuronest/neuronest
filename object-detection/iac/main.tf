terraform {
  required_providers {
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "4.25.0"
    }
  }
  backend "gcs" {
    prefix = "terraform/state"
  }
}
provider "google-beta" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}
resource "google_project" "project" {
  name       = var.project_id
  project_id = var.project_id
  org_id     = var.organization_id
  billing_account = var.billing_account
}

module "base" {
  source                       = "../../shared/iac/modules/services/base"
  project_id                   = var.project_id
  region                       = var.region
  firestore_region             = var.firestore_region
  project_builder_service_account_name = var.project_builder_service_account_name
  mono_repository_name = var.mono_repository_name
}

module "object_detection" {
  source                       = "../../shared/iac/modules/services/object-detection"
  project_id                   = var.project_id
  region                       = var.region
  repository_name              = var.repository_name
  service_account_name         = var.service_account_name
  models_bucket                = var.models_bucket
  package_name                 = var.package_name
}
