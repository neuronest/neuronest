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
  vpc_network                          = var.vpc_network
  psa_range_name                       = var.psa_range_name
  serverless_connector_name            = var.serverless_connector_name
  subnet_name                          = var.subnet_name
  subnet_cidr_range                    = var.subnet_cidr_range
  serverless_connector_cidr            = var.serverless_connector_cidr
  psa_prefix_length                    = var.psa_prefix_length
  min_throughput                       = var.min_throughput
  max_throughput                       = var.max_throughput
}

module "functional_object_detection" {
  source      = "../../shared/iac/modules/services/functional-object-detection"
  project_id  = var.project_id
  region      = var.region
  vpc_network = var.vpc_network
  timezone    = var.timezone

  object_detection_image_name                = var.object_detection_image_name
  object_detection_service_account_name      = var.object_detection_service_account_name
  object_detection_models_bucket             = var.object_detection_models_bucket
  object_detection_samples_bucket            = var.object_detection_samples_bucket
  object_detection_results_bucket            = var.object_detection_results_bucket
  object_detection_model_name                = var.object_detection_model_name
  object_detection_vpc_access_connector      = var.object_detection_vpc_access_connector
  object_detection_cloud_run_name            = var.object_detection_cloud_run_name
  object_detection_cloud_run_memory          = var.object_detection_cloud_run_memory
  object_detection_cloud_run_cpu             = var.object_detection_cloud_run_cpu
  object_detection_cloud_run_min_scale       = var.object_detection_cloud_run_min_scale
  object_detection_cloud_run_max_scale       = var.object_detection_cloud_run_max_scale
  object_detection_firestore_jobs_collection = var.object_detection_firestore_jobs_collection

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
}
