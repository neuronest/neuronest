terraform {
  required_providers {
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "6.18.0"
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

module "functional_database_api" {
  source     = "../../shared/iac/modules/services/functional-database-api"
  project_id = var.project_id
  region     = var.region
  timezone   = var.timezone

  database_api_image_name                                   = var.database_api_image_name
  database_api_cloud_sql_instance_name                      = var.database_api_cloud_sql_instance_name
  database_api_cloud_sql_db_name                            = var.database_api_cloud_sql_db_name
  database_api_cloud_sql_enable_automatic_storage_increases = var.database_api_cloud_sql_enable_automatic_storage_increases
  database_api_cloud_sql_enable_public_ip                   = var.database_api_cloud_sql_enable_public_ip
  database_api_cloud_sql_disk_type                          = var.database_api_cloud_sql_disk_type
  database_api_cloud_sql_database_version                   = var.database_api_cloud_sql_database_version
  database_api_cloud_sql_tier                               = var.database_api_cloud_sql_tier
  database_api_cloud_run_cloud_sql_username                 = var.database_api_cloud_run_cloud_sql_username
  database_api_cloud_run_service_account_name               = var.database_api_cloud_run_service_account_name
  database_api_cloud_run_name                               = var.database_api_cloud_run_name
  database_api_cloud_run_memory                             = var.database_api_cloud_run_memory
  database_api_cloud_run_cpu                                = var.database_api_cloud_run_cpu
  database_api_cloud_run_min_scale                          = var.database_api_cloud_run_min_scale
  database_api_cloud_run_max_scale                          = var.database_api_cloud_run_max_scale


  model_instantiator_image_name                           = var.model_instantiator_image_name
  model_instantiator_webapp_service_account_name          = var.model_instantiator_webapp_service_account_name
  model_instantiator_cloud_scheduler_service_account_name = var.model_instantiator_cloud_scheduler_service_account_name
  model_instantiator_cloud_run_name                       = var.model_instantiator_cloud_run_name
  model_instantiator_cloud_run_memory                     = var.model_instantiator_cloud_run_memory
  model_instantiator_cloud_run_cpu                        = var.model_instantiator_cloud_run_cpu
  model_instantiator_cloud_run_min_scale                  = var.model_instantiator_cloud_run_min_scale
  model_instantiator_cloud_run_max_scale                  = var.model_instantiator_cloud_run_max_scale
  model_instantiator_cloud_scheduler_cloud_sql_job_name   = var.model_instantiator_cloud_scheduler_cloud_sql_job_name
  model_instantiator_cloud_scheduler_cloud_sql_schedule   = var.model_instantiator_cloud_scheduler_cloud_sql_schedule
  model_instantiator_cloud_sql_uninstantiate_route        = var.model_instantiator_cloud_sql_uninstantiate_route
}
