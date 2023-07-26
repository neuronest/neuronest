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
  name            = var.project_id
  project_id      = var.project_id
  org_id          = var.organization_id
  billing_account = var.billing_account
}

module "base" {
  source                               = "../../shared/iac/modules/services/base"
  project_id                           = var.project_id
  region                               = var.region
  firestore_region                     = var.firestore_region
  project_builder_service_account_name = var.project_builder_service_account_name
  mono_repository_name                 = var.mono_repository_name
}

module "video_comparator_functional" {
  source     = "../../shared/iac/modules/services/video-comparator-functional"
  project_id = var.project_id
  region     = var.region
  timezone   = var.timezone
}
