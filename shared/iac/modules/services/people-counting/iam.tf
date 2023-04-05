# Give people_counting_api_sa datastore owner role
resource "google_project_iam_member" "people-counting-api-sa-uses-firestore" {
  project = var.project_id
  role    = "roles/datastore.owner"
  member  = "serviceAccount:${google_service_account.people_counting_api_sa.email}"
}
# Give people_counting_api_sa storage admin role
resource "google_project_iam_member" "people-counting-api-sa-is-storage-admin" {
  project = var.project_id
  role    = "roles/storage.admin"
  member  = "serviceAccount:${google_service_account.people_counting_api_sa.email}"
}
