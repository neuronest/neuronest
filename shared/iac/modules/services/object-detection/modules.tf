module "object_detection" {
  source     = "../../abstract/online-prediction-model"
  project_id = var.project_id
  region     = var.region

  image_name           = var.image_name
  service_account_name = var.service_account_name
  models_bucket        = var.models_bucket
  model_name           = var.model_name

  cloud_run_name      = var.cloud_run_name
  cloud_run_memory    = var.cloud_run_memory
  cloud_run_cpu       = var.cloud_run_cpu
  cloud_run_min_scale = var.cloud_run_min_scale
  cloud_run_max_scale = var.cloud_run_max_scale

  cloud_run_env_vars = merge(
    {
      project_id                = var.project_id
      REGION                    = var.region
      IMAGE_NAME                = var.image_name
      MODEL_NAME                = var.model_name
      FIRESTORE_JOBS_COLLECTION = var.firestore_jobs_collection
      RESULTS_BUCKET            = var.results_bucket
      SAMPLES_BUCKET            = var.samples_bucket
    },
    var.model_instantiator_host != null ? { MODEL_INSTANTIATOR_HOST = var.model_instantiator_host } : {}
  )
}