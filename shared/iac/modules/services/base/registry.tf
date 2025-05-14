#############################################
#    Google Artifact Registry Repository    #
#############################################
#
# Create Artifact Registry Repository for Docker containers
variable "locations" {
  type = list(string)
  default = [
    "europe-west1",
    "europe-west2",
    "europe-west4"
  ]
}

resource "google_artifact_registry_repository" "repository" {
  for_each = toset(var.locations)

  provider      = google-beta
  location      = each.key
  repository_id = "${var.mono_repository_name}-${each.key}"
  format        = "DOCKER"

  cleanup_policies {
    id     = "keep-latest-version"
    action = "KEEP"

    most_recent_versions {
      keep_count = 1
    }
  }
}

