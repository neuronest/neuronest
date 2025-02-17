resource "google_project_iam_member" "object_detection_api_sa_uses_firestore" {
  project = var.project_id
  role    = "roles/datastore.owner"
  member  = "serviceAccount:${module.functional_object_detection.service_account.email}"
}
