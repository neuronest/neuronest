terraform {
  required_providers {
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "4.25.0"
    }
  }
   backend "gcs" {
   prefix  = "terraform/state"
 }
}
provider "google-beta" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}
resource "google_project" "project" {
  name       = var.project_name
  project_id = var.project_id
  org_id     = var.organization_id
}
# Create the bucket where the terraform state is stored
resource "google_storage_bucket" "tfstate_bucket" {
  name          = var.state_bucket
  project = var.project_id
  force_destroy = true
  # location      = var.region
  location      = "europe-west9"
  storage_class = "STANDARD"
  versioning {
    enabled = true
  }
}
module "people_counting" {
  source = "./modules/services/people-counting"
  project_id = var.project_id
  project_name = var.project_name
  region = var.region
  artifact_registry_repository = var.artifact_registry_repository
  webapp_image = var.webapp_image
  firestore_results_collection = var.firestore_results_collection
  videos_to_count_bucket = var.videos_to_count_bucket
  counted_videos_bucket = var.counted_videos_bucket
  location_app_engine = var.location_app_engine
}
