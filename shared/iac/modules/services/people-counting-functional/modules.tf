module "people_counting" {
  source = "../people-counting"
  project_id                   = var.project_id
  region                       = var.region
  repository_name              = var.repository_name
  image_name                   = var.image_name
  webapp_service_account_name  = var.webapp_service_account_name
  firestore_results_collection = var.firestore_results_collection
  videos_to_count_bucket       = var.videos_to_count_bucket
  counted_videos_bucket        = var.counted_videos_bucket
  model_instantiator_host      = var.model_instantiator_host
  object_detection_model_name  = var.object_detection_model_name
  cloud_run_memory             = var.cloud_run_memory
  cloud_run_cpu                = var.cloud_run_cpu
  cloud_run_min_scale          = var.cloud_run_min_scale
  cloud_run_max_scale          = var.cloud_run_max_scale
}