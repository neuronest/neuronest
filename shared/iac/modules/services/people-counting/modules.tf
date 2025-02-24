module "object_detection" {
  source     = "../object-detection"
  project_id = var.project_id
  region     = var.region
  timezone   = var.timezone

  image_name                = var.object_detection_image_name
  service_account_name      = var.object_detection_service_account_name
  models_bucket             = var.object_detection_models_bucket
  samples_bucket            = var.object_detection_samples_bucket
  results_bucket            = var.object_detection_results_bucket
  model_name                = var.object_detection_model_name
  cloud_run_name            = var.object_detection_cloud_run_name
  cloud_run_memory          = var.object_detection_cloud_run_memory
  cloud_run_cpu             = var.object_detection_cloud_run_cpu
  cloud_run_min_scale       = var.object_detection_cloud_run_min_scale
  cloud_run_max_scale       = var.object_detection_cloud_run_max_scale
  cloud_run_timeout         = var.object_detection_cloud_run_timeout
  firestore_jobs_collection = var.object_detection_firestore_jobs_collection
  vertex_location           = var.object_detection_vertex_location

  model_instantiator_image_name                           = var.object_detection_model_instantiator_image_name
  model_instantiator_webapp_service_account_name          = var.object_detection_model_instantiator_webapp_service_account_name
  model_instantiator_cloud_scheduler_service_account_name = var.object_detection_model_instantiator_cloud_scheduler_service_account_name
  model_instantiator_cloud_run_name                       = var.object_detection_model_instantiator_cloud_run_name
  model_instantiator_cloud_run_memory                     = var.object_detection_model_instantiator_cloud_run_memory
  model_instantiator_cloud_run_cpu                        = var.object_detection_model_instantiator_cloud_run_cpu
  model_instantiator_cloud_run_min_scale                  = var.object_detection_model_instantiator_cloud_run_min_scale
  model_instantiator_cloud_run_max_scale                  = var.object_detection_model_instantiator_cloud_run_max_scale
  model_instantiator_cloud_run_timeout                    = var.object_detection_model_instantiator_cloud_run_timeout
  model_instantiator_cloud_scheduler_job_name             = var.object_detection_model_instantiator_cloud_scheduler_job_name
  model_instantiator_cloud_scheduler_schedule             = var.object_detection_model_instantiator_cloud_scheduler_schedule
  model_instantiator_cloud_uninstantiate_route            = var.object_detection_model_instantiator_cloud_uninstantiate_route
}
