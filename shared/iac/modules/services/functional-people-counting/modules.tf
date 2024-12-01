module "functional_object_detection" {
  source      = "../../abstract/functional-online-prediction-model"
  project_id  = var.project_id
  region      = var.region
  timezone    = var.timezone
  vpc_network = var.vpc_network

  online_prediction_model_image_name           = var.object_detection_image_name
  online_prediction_model_service_account_name = var.object_detection_service_account_name
  online_prediction_model_models_bucket        = var.object_detection_models_bucket
  online_prediction_model_samples_bucket       = var.object_detection_samples_bucket
  online_prediction_model_results_bucket       = var.object_detection_results_bucket
  online_prediction_model_model_name           = var.object_detection_model_name
  online_prediction_model_vpc_access_connector = var.object_detection_vpc_access_connector
  online_prediction_model_cloud_run_name       = var.object_detection_cloud_run_name
  online_prediction_model_cloud_run_memory     = var.object_detection_cloud_run_memory
  online_prediction_model_cloud_run_cpu        = var.object_detection_cloud_run_cpu
  online_prediction_model_cloud_run_min_scale  = var.object_detection_cloud_run_min_scale
  online_prediction_model_cloud_run_max_scale  = var.object_detection_cloud_run_max_scale

  online_prediction_model_cloud_run_env_vars = {
    PROJECT_ID                = var.project_id
    REGION                    = var.region
    VPC_NETWORK               = var.vpc_network
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
  model_instantiator_cloud_scheduler_job_name             = var.model_instantiator_cloud_scheduler_job_name
  model_instantiator_cloud_scheduler_schedule             = var.model_instantiator_cloud_scheduler_schedule
  model_instantiator_cloud_uninstantiate_route            = var.model_instantiator_cloud_uninstantiate_route
}
module "people_counting" {
  source                    = "../people-counting"
  project_id                = var.project_id
  region                    = var.region
  vpc_network               = var.vpc_network
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

  model_instantiator_host     = module.functional_object_detection.model_instantiator_url
  object_detection_model_name = module.functional_object_detection.model_name
}
