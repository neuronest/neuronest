module "video_comparator" {
  source     = "../../abstract/online-prediction-model"
  project_id = var.project_id
  region     = var.region
  timezone   = var.timezone

  vertex_location = var.vertex_location

  image_name           = var.image_name
  service_account_name = var.service_account_name
  models_bucket        = var.models_bucket
  samples_bucket       = var.samples_bucket
  results_bucket       = var.results_bucket
  model_name           = var.model_name
  cloud_run_name       = var.cloud_run_name
  cloud_run_memory     = var.cloud_run_memory
  cloud_run_cpu        = var.cloud_run_cpu
  cloud_run_min_scale  = var.cloud_run_min_scale
  cloud_run_max_scale  = var.cloud_run_max_scale
  cloud_run_timeout    = var.cloud_run_timeout

  cloud_run_env_vars = {
    PROJECT_ID                = var.project_id
    REGION                    = var.region
    IMAGE_NAME                = var.image_name
    MODEL_NAME                = var.model_name
    FIRESTORE_JOBS_COLLECTION = var.firestore_jobs_collection
    EMBEDDINGS_BUCKET         = var.embeddings_bucket
    RESULTS_BUCKET            = var.results_bucket
    SAMPLES_BUCKET            = var.samples_bucket
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
