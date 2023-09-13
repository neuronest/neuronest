module "object_detection_functional" {
  source                                                  = "../functional-object-detection"
  project_id                                              = var.project_id
  region                                                  = var.region
  timezone                                                = var.timezone
  object_detection_service_account_name                   = var.object_detection_service_account_name
  object_detection_models_bucket                          = var.object_detection_models_bucket
  object_detection_model_name                             = var.object_detection_model_name
  model_instantiator_image_name                           = var.object_detection_model_instantiator_image_name
  model_instantiator_webapp_service_account_name          = var.object_detection_model_instantiator_webapp_service_account_name
  model_instantiator_cloud_scheduler_service_account_name = var.object_detection_model_instantiator_cloud_scheduler_service_account_name
  model_instantiator_cloud_run_name                       = var.object_detection_model_instantiator_cloud_run_name
  model_instantiator_cloud_run_memory                     = var.object_detection_model_instantiator_cloud_run_memory
  model_instantiator_cloud_run_cpu                        = var.object_detection_model_instantiator_cloud_run_cpu
  model_instantiator_cloud_run_min_scale                  = var.object_detection_model_instantiator_cloud_run_min_scale
  model_instantiator_cloud_run_max_scale                  = var.object_detection_model_instantiator_cloud_run_max_scale
  model_instantiator_cloud_scheduler_job_name             = var.object_detection_model_instantiator_cloud_scheduler_job_name
  model_instantiator_cloud_scheduler_schedule             = var.object_detection_model_instantiator_cloud_scheduler_schedule
  model_instantiator_cloud_uninstantiate_route            = var.object_detection_model_instantiator_cloud_uninstantiate_route
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

  model_instantiator_host     = module.object_detection_functional.model_instantiator_url
  object_detection_model_name = module.object_detection_functional.model_name
}
