#module "functional_object_detection" {
#  source     = "../../abstract/functional-online-prediction-model"
#  project_id = var.project_id
#  region     = var.region
#  timezone   = var.timezone
#
#  online_prediction_model_service_account_name = var.object_detection_service_account_name
#  online_prediction_model_models_bucket        = var.object_detection_models_bucket
#  online_prediction_model_model_name           = var.object_detection_model_name
#
#  model_instantiator_image_name                           = var.model_instantiator_image_name
#  model_instantiator_webapp_service_account_name          = var.model_instantiator_webapp_service_account_name
#  model_instantiator_cloud_scheduler_service_account_name = var.model_instantiator_cloud_scheduler_service_account_name
#  model_instantiator_cloud_run_name                       = var.model_instantiator_cloud_run_name
#  model_instantiator_cloud_run_memory                     = var.model_instantiator_cloud_run_memory
#  model_instantiator_cloud_run_cpu                        = var.model_instantiator_cloud_run_cpu
#  model_instantiator_cloud_run_min_scale                  = var.model_instantiator_cloud_run_min_scale
#  model_instantiator_cloud_run_max_scale                  = var.model_instantiator_cloud_run_max_scale
#  model_instantiator_cloud_scheduler_job_name             = var.model_instantiator_cloud_scheduler_job_name
#  model_instantiator_cloud_scheduler_schedule             = var.model_instantiator_cloud_scheduler_schedule
#  model_instantiator_cloud_uninstantiate_route            = var.model_instantiator_cloud_uninstantiate_route
#}

module "database_api" {
  source                         = "../database-api"
  project_id                     = var.project_id
  region                         = var.region
  image_name                     = var.database_api_image_name
  cloud_sql_instance_name        = var.database_api_cloud_sql_instance_name
  cloud_sql_db_name              = var.database_api_cloud_sql_db_name
  cloud_run_cloud_sql_username   = var.database_api_cloud_run_cloud_sql_username
  cloud_run_service_account_name = var.database_api_cloud_run_service_account_name
  cloud_run_name                 = var.database_api_cloud_run_name
  cloud_run_memory               = var.database_api_cloud_run_memory
  cloud_run_cpu                  = var.database_api_cloud_run_cpu
  cloud_run_min_scale            = var.database_api_cloud_run_min_scale
  cloud_run_max_scale            = var.database_api_cloud_run_max_scale
}
