resource "google_cloud_run_service_iam_member" "allow_online_prediction_model" {
  service  = module.model_instantiator.cloud_run_name
  location = var.region
  role     = "roles/run.invoker"
  member   = "serviceAccount:${module.online_prediction_model.service_account.email}"
}
