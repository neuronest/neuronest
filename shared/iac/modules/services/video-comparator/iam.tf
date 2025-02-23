resource "google_project_iam_member" "video_comparator_api_sa_uses_firestore" {
  project = var.project_id
  role    = "roles/datastore.owner"
  member  = "serviceAccount:${module.video_comparator.service_account.email}"
}
