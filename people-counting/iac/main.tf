terraform {
  required_providers {
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "4.46.0"
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

module "people_counting" {
  source     = "../../shared/iac/modules/services/people-counting"
  project_id = var.project_id
  region     = var.region
  timezone   = var.timezone

  vertex_location = var.vertex_location

  image_name                = var.image_name
  service_account_name      = var.service_account_name
  results_bucket            = var.results_bucket
  firestore_jobs_collection = var.firestore_jobs_collection
  samples_bucket            = var.samples_bucket
  counted_videos_bucket     = var.counted_videos_bucket
  model_instantiator_host   = var.model_instantiator_host
  cloud_run_name            = var.cloud_run_name
  cloud_run_memory          = var.cloud_run_memory
  cloud_run_cpu             = var.cloud_run_cpu
  cloud_run_min_scale       = var.cloud_run_min_scale
  cloud_run_max_scale       = var.cloud_run_max_scale
  cloud_run_timeout         = var.cloud_run_timeout

  object_detection_image_name                = var.object_detection_image_name
  object_detection_service_account_name      = var.object_detection_service_account_name
  object_detection_models_bucket             = var.object_detection_models_bucket
  object_detection_samples_bucket            = var.object_detection_samples_bucket
  object_detection_results_bucket            = var.object_detection_results_bucket
  object_detection_model_name                = var.object_detection_model_name
  object_detection_cloud_run_name            = var.object_detection_cloud_run_name
  object_detection_cloud_run_memory          = var.object_detection_cloud_run_memory
  object_detection_cloud_run_cpu             = var.object_detection_cloud_run_cpu
  object_detection_cloud_run_min_scale       = var.object_detection_cloud_run_min_scale
  object_detection_cloud_run_max_scale       = var.object_detection_cloud_run_max_scale
  object_detection_cloud_run_timeout         = var.object_detection_cloud_run_timeout
  object_detection_firestore_jobs_collection = var.object_detection_firestore_jobs_collection

  object_detection_model_instantiator_image_name                           = var.object_detection_model_instantiator_image_name
  object_detection_model_instantiator_webapp_service_account_name          = var.object_detection_model_instantiator_webapp_service_account_name
  object_detection_model_instantiator_cloud_scheduler_service_account_name = var.object_detection_model_instantiator_cloud_scheduler_service_account_name
  object_detection_model_instantiator_cloud_run_name                       = var.object_detection_model_instantiator_cloud_run_name
  object_detection_model_instantiator_cloud_run_memory                     = var.object_detection_model_instantiator_cloud_run_memory
  object_detection_model_instantiator_cloud_run_cpu                        = var.object_detection_model_instantiator_cloud_run_cpu
  object_detection_model_instantiator_cloud_run_min_scale                  = var.object_detection_model_instantiator_cloud_run_min_scale
  object_detection_model_instantiator_cloud_run_max_scale                  = var.object_detection_model_instantiator_cloud_run_max_scale
  object_detection_model_instantiator_cloud_run_timeout                    = var.object_detection_model_instantiator_cloud_run_timeout
  object_detection_model_instantiator_cloud_scheduler_job_name             = var.object_detection_model_instantiator_cloud_scheduler_job_name
  object_detection_model_instantiator_cloud_scheduler_schedule             = var.object_detection_model_instantiator_cloud_scheduler_schedule
  object_detection_model_instantiator_cloud_uninstantiate_route            = var.object_detection_model_instantiator_cloud_uninstantiate_route
}
