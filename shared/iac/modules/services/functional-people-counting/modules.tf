module "functional_object_detection" {
  source     = "../functional-object-detection"
  project_id = var.project_id
  region     = var.region
  timezone   = var.timezone

  vertex_location = var.vertex_location

  object_detection_image_name                = var.object_detection_image_name
  object_detection_service_account_name      = var.object_detection_service_account_name
  object_detection_models_bucket             = var.object_detection_models_bucket
  object_detection_samples_bucket            = var.object_detection_samples_bucket
  object_detection_results_bucket            = var.object_detection_results_bucket
  object_detection_model_name                = var.object_detection_model_name
  object_detection_cloud_run_name            = var.object_detection_cloud_run_name
  object_detection_cloud_run_memory          = var.object_detection_cloud_run_memory
  object_detection_cloud_run_cpu             = var.object_detection_cloud_run_cpu
  object_detection_cloud_run_min_scale       = var.object_detection_cloud_run_min_scale
  object_detection_cloud_run_max_scale       = var.object_detection_cloud_run_max_scale
  object_detection_cloud_run_timeout         = var.object_detection_cloud_run_timeout
  object_detection_firestore_jobs_collection = var.object_detection_firestore_jobs_collection

  model_instantiator_image_name                           = var.model_instantiator_image_name
  model_instantiator_webapp_service_account_name          = var.model_instantiator_webapp_service_account_name
  model_instantiator_cloud_scheduler_service_account_name = var.model_instantiator_cloud_scheduler_service_account_name
  model_instantiator_cloud_run_name                       = var.model_instantiator_cloud_run_name
  model_instantiator_cloud_run_memory                     = var.model_instantiator_cloud_run_memory
  model_instantiator_cloud_run_cpu                        = var.model_instantiator_cloud_run_cpu
  model_instantiator_cloud_run_min_scale                  = var.model_instantiator_cloud_run_min_scale
  model_instantiator_cloud_run_max_scale                  = var.model_instantiator_cloud_run_max_scale
  model_instantiator_cloud_run_timeout                    = var.model_instantiator_cloud_run_timeout
  model_instantiator_cloud_scheduler_job_name             = var.model_instantiator_cloud_scheduler_job_name
  model_instantiator_cloud_scheduler_schedule             = var.model_instantiator_cloud_scheduler_schedule
  model_instantiator_cloud_uninstantiate_route            = var.model_instantiator_cloud_uninstantiate_route
}
module "people_counting" {
  source                    = "../people-counting"
  project_id                = var.project_id
  region                    = var.region
  image_name                = var.people_counting_image_name
  service_account_name      = var.people_counting_service_account_name
  results_bucket            = var.people_counting_results_bucket
  firestore_jobs_collection = var.people_counting_firestore_jobs_collection
  samples_bucket            = var.people_counting_samples_bucket
  counted_videos_bucket     = var.people_counting_counted_videos_bucket
  cloud_run_name            = var.people_counting_cloud_run_name
  cloud_run_memory          = var.people_counting_cloud_run_memory
  cloud_run_cpu             = var.people_counting_cloud_run_cpu
  cloud_run_min_scale       = var.people_counting_cloud_run_min_scale
  cloud_run_max_scale       = var.people_counting_cloud_run_max_scale
  cloud_run_timeout         = var.people_counting_cloud_run_timeout

  object_detection_host = module.functional_object_detection.online_prediction_model_url
}
