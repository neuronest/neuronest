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

module "model_instantiator" {
  source                               = "../../shared/iac/modules/services/model-instantiator"
  project_id                           = var.project_id
  region                               = var.region
  timezone                             = var.timezone
  image_name                           = var.image_name
  webapp_service_account_name          = var.webapp_service_account_name
  cloud_scheduler_service_account_name = var.cloud_scheduler_service_account_name
  cloud_run_name                       = var.cloud_run_name
  cloud_run_memory                     = var.cloud_run_memory
  cloud_run_cpu                        = var.cloud_run_cpu
  cloud_run_min_scale                  = var.cloud_run_min_scale
  cloud_run_max_scale                  = var.cloud_run_max_scale
  cloud_scheduler_job_name             = var.cloud_scheduler_job_name
  cloud_scheduler_schedule             = var.cloud_scheduler_schedule
  cloud_uninstantiate_route            = var.cloud_uninstantiate_route
  cloud_scheduler_model_name           = var.cloud_scheduler_model_name
}
