resource "google_service_account" "infrastructure_builder_sa" {
  provider     = google-beta
  account_id   = var.base_service_account_name
  display_name = "Infrastructure builder Service Account"
}
resource "google_service_account_key" "infrastructure_builder_key" {
  service_account_id = google_service_account.infrastructure_builder_sa.name
  public_key_type    = "TYPE_X509_PEM_FILE"
}
