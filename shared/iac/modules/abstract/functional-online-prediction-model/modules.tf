module "online_prediction_model" {
  source               = "../online-prediction-model"
  project_id           = var.project_id
  region               = var.region
  service_account_name = var.online_prediction_model_service_account_name
  models_bucket        = var.online_prediction_model_models_bucket
  model_name           = var.online_prediction_model_model_name
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
  cloud_scheduler_job_name             = var.model_instantiator_cloud_scheduler_job_name
  cloud_scheduler_schedule             = var.model_instantiator_cloud_scheduler_schedule
  cloud_uninstantiate_route            = var.model_instantiator_cloud_uninstantiate_route

  cloud_scheduler_model_name      = module.online_prediction_model.model_name
  online_prediction_model_sa_name = module.online_prediction_model.service_account_name
}
