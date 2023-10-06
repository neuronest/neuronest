module "object_detection" {
  source               = "../object-detection"
  project_id           = var.project_id
  region               = var.region
  service_account_name = var.object_detection_service_account_name
  models_bucket        = var.object_detection_models_bucket
  model_name           = var.object_detection_model_name
}
module "model_instantiator" {
  source                               = "../model-instantiator"
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

  cloud_scheduler_model_name      = module.object_detection.model_name
  online_prediction_model_sa_name = module.object_detection.service_account_name
}
module "people_counting" {
  source                       = "../people-counting"
  project_id                   = var.project_id
  region                       = var.region
  image_name                   = var.people_counting_image_name
  service_account_name         = var.people_counting_service_account_name
  firestore_results_collection = var.people_counting_firestore_results_collection
  videos_to_count_bucket       = var.people_counting_videos_to_count_bucket
  counted_videos_bucket        = var.people_counting_counted_videos_bucket
  cloud_run_name               = var.people_counting_cloud_run_name
  cloud_run_memory             = var.people_counting_cloud_run_memory
  cloud_run_cpu                = var.people_counting_cloud_run_cpu
  cloud_run_min_scale          = var.people_counting_cloud_run_min_scale
  cloud_run_max_scale          = var.people_counting_cloud_run_max_scale

  model_instantiator_host     = module.model_instantiator.url
  object_detection_model_name = module.object_detection.model_name
}