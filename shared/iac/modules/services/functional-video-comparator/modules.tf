module "functional_video_comparator" {
  source     = "../../abstract/functional-online-prediction-model"
  project_id = var.project_id
  region     = var.region
  timezone   = var.timezone

  online_prediction_model_service_account_name = var.video_comparator_service_account_name
  online_prediction_model_models_bucket        = var.video_comparator_models_bucket
  online_prediction_model_model_name           = var.video_comparator_model_name
  online_prediction_model_cloud_run_name       = var.video_comparator_cloud_run_name
  online_prediction_model_cloud_run_memory     = var.video_comparator_cloud_run_memory
  online_prediction_model_cloud_run_cpu        = var.video_comparator_cloud_run_cpu
  online_prediction_model_cloud_run_image_name = var.video_comparator_cloud_run_image_name
  online_prediction_model_cloud_run_min_scale  = var.video_comparator_cloud_run_min_scale
  online_prediction_model_cloud_run_max_scale  = var.video_comparator_cloud_run_max_scale

  online_prediction_model_cloud_run_env_vars = {
    PROJECT_ID = var.project_id
    REGION = var.region
    IMAGE_NAME = var.video_comparator_cloud_run_image_name
    MODEL_NAME = var.video_comparator_model_name
    FIRESTORE_JOBS_COLLECTION = var.video_comparator_firestore_jobs_collection
    EMBEDDINGS_BUCKET = var.video_comparator_embeddings_bucket
    JOB_RESULTS_BUCKET = var.video_comparator_job_results_bucket
    VIDEOS_TO_COMPARE_BUCKET = var.video_comparator_videos_to_compare_bucket
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
