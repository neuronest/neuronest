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

module "functional_people_counting" {
  source     = "../../shared/iac/modules/services/functional-people-counting"
  project_id = var.project_id
  region     = var.region
  timezone   = var.timezone

  people_counting_image_name                   = var.people_counting_image_name
  people_counting_service_account_name         = var.people_counting_service_account_name
  people_counting_firestore_results_collection = var.people_counting_firestore_results_collection
  people_counting_firestore_jobs_collection    = var.people_counting_firestore_jobs_collection
  people_counting_videos_to_count_bucket       = var.people_counting_videos_to_count_bucket
  people_counting_counted_videos_bucket        = var.people_counting_counted_videos_bucket
  people_counting_model_instantiator_host      = var.people_counting_model_instantiator_host
  people_counting_object_detection_model_name  = var.people_counting_object_detection_model_name
  people_counting_cloud_run_name               = var.people_counting_cloud_run_name
  people_counting_cloud_run_memory             = var.people_counting_cloud_run_memory
  people_counting_cloud_run_cpu                = var.people_counting_cloud_run_cpu
  people_counting_cloud_run_min_scale          = var.people_counting_cloud_run_min_scale
  people_counting_cloud_run_max_scale          = var.people_counting_cloud_run_max_scale

  object_detection_service_account_name = var.object_detection_service_account_name
  object_detection_models_bucket        = var.object_detection_models_bucket
  object_detection_model_name           = var.object_detection_model_name

  model_instantiator_image_name                           = var.model_instantiator_image_name
  model_instantiator_webapp_service_account_name          = var.model_instantiator_webapp_service_account_name
  model_instantiator_cloud_scheduler_service_account_name = var.model_instantiator_cloud_scheduler_service_account_name
  model_instantiator_cloud_run_name                       = var.model_instantiator_cloud_run_name
  model_instantiator_cloud_run_memory                     = var.model_instantiator_cloud_run_memory
  model_instantiator_cloud_run_cpu                        = var.model_instantiator_cloud_run_cpu
  model_instantiator_cloud_run_min_scale                  = var.model_instantiator_cloud_run_min_scale
  model_instantiator_cloud_run_max_scale                  = var.model_instantiator_cloud_run_max_scale
  model_instantiator_cloud_scheduler_job_name             = var.model_instantiator_cloud_scheduler_job_name
  model_instantiator_cloud_scheduler_schedule             = var.model_instantiator_cloud_scheduler_schedule
  model_instantiator_cloud_uninstantiate_route            = var.model_instantiator_cloud_uninstantiate_route

  service_evaluator_image_name                           = var.service_evaluator_image_name
  service_evaluator_webapp_service_account_name          = var.service_evaluator_webapp_service_account_name
  service_evaluator_firestore_jobs_collection            = var.service_evaluator_firestore_jobs_collection
  service_evaluator_serialized_service_client_parameters = var.service_evaluator_serialized_service_client_parameters
  service_evaluator_service_image_name                   = var.service_evaluator_service_image_name
  service_evaluator_service_name                         = var.service_evaluator_service_name
  service_evaluator_job_prefix_name                      = var.service_evaluator_job_prefix_name
  service_evaluator_cloud_run_name                       = var.service_evaluator_cloud_run_name
  service_evaluator_cloud_run_memory                     = var.service_evaluator_cloud_run_memory
  service_evaluator_cloud_run_cpu                        = var.service_evaluator_cloud_run_cpu
  service_evaluator_cloud_run_min_scale                  = var.service_evaluator_cloud_run_min_scale
  service_evaluator_cloud_run_max_scale                  = var.service_evaluator_cloud_run_max_scale
}
