terraform {
  required_providers {
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "6.35.0"
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

module "object_detection" {
  source     = "../../shared/iac/modules/services/object-detection"
  project_id = var.project_id
  region     = var.region
  timezone   = var.timezone

  image_name                = var.image_name
  service_account_name      = var.service_account_name
  models_bucket             = var.models_bucket
  samples_bucket            = var.samples_bucket
  results_bucket            = var.results_bucket
  model_name                = var.model_name
  cloud_run_name            = var.cloud_run_name
  cloud_run_memory          = var.cloud_run_memory
  cloud_run_cpu             = var.cloud_run_cpu
  cloud_run_min_scale       = var.cloud_run_min_scale
  cloud_run_max_scale       = var.cloud_run_max_scale
  cloud_run_timeout         = var.cloud_run_timeout
  firestore_jobs_collection = var.firestore_jobs_collection
  vertex_location           = var.vertex_location

  model_instantiator_image_name                           = var.model_instantiator_image_name
  model_instantiator_webapp_service_account_name          = var.model_instantiator_webapp_service_account_name
  model_instantiator_cloud_scheduler_service_account_name = var.model_instantiator_cloud_scheduler_service_account_name
  model_instantiator_cloud_run_name                       = var.model_instantiator_cloud_run_name
  model_instantiator_cloud_run_memory                     = var.model_instantiator_cloud_run_memory
  model_instantiator_cloud_run_cpu                        = var.model_instantiator_cloud_run_cpu
  model_instantiator_cloud_run_min_scale                  = var.model_instantiator_cloud_run_min_scale
  model_instantiator_cloud_run_max_scale                  = var.model_instantiator_cloud_run_max_scale
  model_instantiator_cloud_run_timeout                    = var.model_instantiator_cloud_run_timeout
  model_instantiator_cloud_scheduler_job_name             = var.model_instantiator_cloud_scheduler_job_name
  model_instantiator_cloud_scheduler_schedule             = var.model_instantiator_cloud_scheduler_schedule
  model_instantiator_cloud_uninstantiate_route            = var.model_instantiator_cloud_uninstantiate_route
}
