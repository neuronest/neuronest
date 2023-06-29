resource "google_cloud_scheduler_job" "uninstantiate_job" {
  provider  = google-beta
  name      = var.cloud_scheduler_job_name
  schedule  = var.cloud_scheduler_schedule
  time_zone = var.timezone

  http_target {
    http_method = "POST"
    uri         = format("%s%s", google_cloud_run_service.model_instantiator_api.status[0].url, var.cloud_uninstantiate_route)
    body        = base64encode("{\"model_name\": \"${var.cloud_scheduler_model_name}\"}")
    headers = {
      "Content-Type" : "application/json; charset=utf-8"
      "User-Agent" : "Google-Cloud-Scheduler"
    }

    oidc_token {
      service_account_email = google_service_account.model_instantiator_cloud_scheduler_sa.email
    }
  }
}
