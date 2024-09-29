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

module "video_comparator" {
  source                    = "../../shared/iac/modules/services/video-comparator"
  project_id                = var.project_id
  region                    = var.region
  model_image_name          = var.model_image_name
  service_account_name      = var.webapp_service_account_name
  firestore_jobs_collection = var.firestore_jobs_collection
  samples_bucket            = var.samples_bucket
  embeddings_bucket         = var.embeddings_bucket
  results_bucket            = var.results_bucket
  model_instantiator_host   = var.model_instantiator_host
  models_bucket             = var.models_bucket
  model_name                = var.model_name
  cloud_run_name            = var.cloud_run_name
  cloud_run_memory          = var.cloud_run_memory
  cloud_run_cpu             = var.cloud_run_cpu
  cloud_run_image_name      = var.cloud_run_image_name
  cloud_run_min_scale       = var.cloud_run_min_scale
  cloud_run_max_scale       = var.cloud_run_max_scale
}
