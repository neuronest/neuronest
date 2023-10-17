module "video_comparator" {
  source     = "../../abstract/online-prediction-model"
  project_id = var.project_id
  region     = var.region

  service_account_name = var.service_account_name
  models_bucket        = var.models_bucket
  model_name           = var.model_name
}
