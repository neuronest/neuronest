module "database_api" {
  source                                       = "../database-api"
  project_id                                   = var.project_id
  region                                       = var.region
  image_name                                   = var.database_api_image_name
  cloud_sql_instance_name                      = var.database_api_cloud_sql_instance_name
  cloud_sql_db_name                            = var.database_api_cloud_sql_db_name
  cloud_sql_enable_automatic_storage_increases = var.database_api_cloud_sql_enable_automatic_storage_increases
  cloud_sql_enable_public_ip                   = var.database_api_cloud_sql_enable_public_ip
  cloud_sql_disk_type                          = var.database_api_cloud_sql_disk_type
  cloud_sql_database_version                   = var.database_api_cloud_sql_database_version
  cloud_sql_tier                               = var.database_api_cloud_sql_tier
  cloud_run_cloud_sql_username                 = var.database_api_cloud_run_cloud_sql_username
  cloud_run_service_account_name               = var.database_api_cloud_run_service_account_name
  cloud_run_name                               = var.database_api_cloud_run_name
  cloud_run_memory                             = var.database_api_cloud_run_memory
  cloud_run_cpu                                = var.database_api_cloud_run_cpu
  cloud_run_min_scale                          = var.database_api_cloud_run_min_scale
  cloud_run_max_scale                          = var.database_api_cloud_run_max_scale
}
module "model_instantiator" {
  source                               = "../../services/model-instantiator"
  project_id                           = var.project_id
  region                               = var.region
  timezone                             = var.timezone
  image_name                           = var.model_instantiator_image_name
  webapp_service_account_name          = var.model_instantiator_webapp_service_account_name
  cloud_scheduler_service_account_name = var.model_instantiator_cloud_scheduler_service_account_name
  cloud_run_name                       = var.model_instantiator_cloud_run_name
  cloud_run_memory                     = var.model_instantiator_cloud_run_memory
  cloud_run_cpu                        = var.model_instantiator_cloud_run_cpu
  cloud_run_min_scale                  = var.model_instantiator_cloud_run_min_scale
  cloud_run_max_scale                  = var.model_instantiator_cloud_run_max_scale


  # cloud_scheduler_job_name             = var.model_instantiator_cloud_scheduler_job_name
  cloud_scheduler_cloud_sql_job_name = var.model_instantiator_cloud_scheduler_cloud_sql_job_name

  # cloud_scheduler_schedule             = var.model_instantiator_cloud_scheduler_schedule
  cloud_scheduler_cloud_sql_schedule = var.model_instantiator_cloud_scheduler_cloud_sql_schedule

  # cloud_uninstantiate_route            = var.model_instantiator_cloud_uninstantiate_route
  cloud_sql_uninstantiate_route = var.model_instantiator_cloud_sql_uninstantiate_route

  cloud_scheduler_cloud_sql_instance_name = module.database_api.cloud_sql_instance_name

  # online_prediction_model_sa_name = module.online_prediction_model.service_account_name
}
