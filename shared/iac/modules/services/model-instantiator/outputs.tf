output "cloud_run_name" {
  value = var.cloud_run_name
}
output "url" {
  value = google_cloud_run_v2_service.model_instantiator_api.uri
}
output "cloud_scheduler_job_name" {
  value = google_cloud_scheduler_job.uninstantiate_job.name
}
