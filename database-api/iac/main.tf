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
  source     = "../../shared/iac/modules/services/database-api"
  project_id = var.project_id
  region     = var.region
  timezone   = var.timezone

  image_name                                   = var.image_name
  cloud_sql_instance_name                      = var.cloud_sql_instance_name
  cloud_sql_db_name                            = var.cloud_sql_db_name
  cloud_sql_enable_automatic_storage_increases = var.cloud_sql_enable_automatic_storage_increases
  cloud_sql_enable_public_ip                   = var.cloud_sql_enable_public_ip
  cloud_sql_disk_type                          = var.cloud_sql_disk_type
  cloud_sql_database_version                   = var.cloud_sql_database_version
  cloud_sql_tier                               = var.cloud_sql_tier
  cloud_run_cloud_sql_username                 = var.cloud_run_cloud_sql_username
  cloud_run_service_account_name               = var.cloud_run_service_account_name
  cloud_run_name                               = var.cloud_run_name
  cloud_run_memory                             = var.cloud_run_memory
  cloud_run_cpu                                = var.cloud_run_cpu
  cloud_run_min_scale                          = var.cloud_run_min_scale
  cloud_run_max_scale                          = var.cloud_run_max_scale


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
  model_instantiator_cloud_run_timeout                    = var.model_instantiator_cloud_run_timeout
}
