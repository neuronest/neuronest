module "model_instantiator" {
  source     = "../../services/model-instantiator"
  project_id = var.project_id
  region     = var.region
  timezone   = var.timezone

  vertex_location = var.vertex_location

  image_name                           = var.model_instantiator_image_name
  webapp_service_account_name          = var.model_instantiator_webapp_service_account_name
  cloud_scheduler_service_account_name = var.model_instantiator_cloud_scheduler_service_account_name
  cloud_run_name                       = var.model_instantiator_cloud_run_name
  cloud_run_memory                     = var.model_instantiator_cloud_run_memory
  cloud_run_cpu                        = var.model_instantiator_cloud_run_cpu
  cloud_run_min_scale                  = var.model_instantiator_cloud_run_min_scale
  cloud_run_max_scale                  = var.model_instantiator_cloud_run_max_scale
  cloud_run_timeout                    = var.model_instantiator_cloud_run_timeout

  cloud_scheduler_job_name  = var.model_instantiator_cloud_scheduler_job_name
  cloud_scheduler_schedule  = var.model_instantiator_cloud_scheduler_schedule
  cloud_uninstantiate_route = var.model_instantiator_cloud_uninstantiate_route

  cloud_scheduler_model_name      = var.model_name
  online_prediction_model_sa_name = google_service_account.online_prediction_model_sa.name
}
