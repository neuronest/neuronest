module "functional_object_detection" {
  source     = "../../abstract/functional-online-prediction-model"
  project_id = var.project_id
  region     = var.region
  timezone   = var.timezone

  vertex_location = var.vertex_location

  online_prediction_model_image_name           = var.object_detection_image_name
  online_prediction_model_service_account_name = var.object_detection_service_account_name
  online_prediction_model_models_bucket        = var.object_detection_models_bucket
  online_prediction_model_samples_bucket       = var.object_detection_samples_bucket
  online_prediction_model_results_bucket       = var.object_detection_results_bucket
  online_prediction_model_model_name           = var.object_detection_model_name
  online_prediction_model_cloud_run_name       = var.object_detection_cloud_run_name
  online_prediction_model_cloud_run_memory     = var.object_detection_cloud_run_memory
  online_prediction_model_cloud_run_cpu        = var.object_detection_cloud_run_cpu
  online_prediction_model_cloud_run_min_scale  = var.object_detection_cloud_run_min_scale
  online_prediction_model_cloud_run_max_scale  = var.object_detection_cloud_run_max_scale
  online_prediction_model_cloud_run_timeout    = var.object_detection_cloud_run_timeout

  online_prediction_model_cloud_run_env_vars = {
    PROJECT_ID                = var.project_id
    REGION                    = var.region
    IMAGE_NAME                = var.object_detection_image_name
    MODEL_NAME                = var.object_detection_model_name
    FIRESTORE_JOBS_COLLECTION = var.object_detection_firestore_jobs_collection
    RESULTS_BUCKET            = var.object_detection_results_bucket
    SAMPLES_BUCKET            = var.object_detection_samples_bucket
  }

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
