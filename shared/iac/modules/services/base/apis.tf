
##############################################
##               Enable APIs                #
##############################################
resource "google_project_service" "enable_apis" {
  for_each = toset([
    "cloudbilling.googleapis.com",
    "iam.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "firestore.googleapis.com",
    "appengine.googleapis.com",
    "servicenetworking.googleapis.com",
    "vpcaccess.googleapis.com",
    "dns.googleapis.com"
  ])
  project            = var.project_id
  service            = each.key
  disable_on_destroy = false
}

# This is used so there is some time for the activation of the APIs to propagate through
# Google Cloud before actually calling them.
resource "time_sleep" "api_activation_waiting" {
  create_duration = "120s"
  depends_on = [
    google_project_service.enable_apis
  ]
}
