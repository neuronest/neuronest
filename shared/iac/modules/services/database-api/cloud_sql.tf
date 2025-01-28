##############################################
#       Cloud SQL PostgreSQL Instance        #
##############################################

# Ensure Cloud SQL Instance is running before applying changes
resource "null_resource" "ensure_instance_is_running" {
  triggers = {
    instance_name     = var.cloud_sql_instance_name
    database_version  = var.cloud_sql_database_version
    region            = var.region
    tier              = var.cloud_sql_tier
    disk_type         = var.cloud_sql_disk_type
    project_id        = var.project_id
    enable_public_ip  = var.cloud_sql_enable_public_ip
    enable_autoresize = var.cloud_sql_enable_automatic_storage_increases
  }

  provisioner "local-exec" {
    command = <<EOT
      set -e
      chmod +x ${path.module}/scripts/ensure_cloud_sql_is_started.sh && \
      ${path.module}/scripts/ensure_cloud_sql_is_started.sh ${self.triggers.instance_name} ${self.triggers.project_id}
    EOT

  }

}

# Cloud SQL Instance for PostgreSQL 12
resource "google_sql_database_instance" "neuronest_instance" {
  provider         = google-beta
  depends_on       = [null_resource.ensure_instance_is_running] # Ensure the instance is running before proceeding
  name             = null_resource.ensure_instance_is_running.triggers.instance_name
  database_version = null_resource.ensure_instance_is_running.triggers.database_version
  region           = null_resource.ensure_instance_is_running.triggers.region
  settings {
    tier = null_resource.ensure_instance_is_running.triggers.tier
    backup_configuration {
      enabled = false # Backups disabled
    }
    ip_configuration {
      ipv4_enabled = null_resource.ensure_instance_is_running.triggers.enable_public_ip
    }
    disk_type       = null_resource.ensure_instance_is_running.triggers.disk_type
    disk_autoresize = null_resource.ensure_instance_is_running.triggers.enable_autoresize
  }
}

# Create the PostgreSQL Database
resource "google_sql_database" "neuronest_database" {
  name     = var.cloud_sql_db_name
  instance = google_sql_database_instance.neuronest_instance.name
}

# Generate and store the database password in Secret Manager
resource "random_password" "database_api_db_password" {
  length  = 16
  special = true
}

resource "google_secret_manager_secret" "database_api_db_password_secret" {
  secret_id = "database_api_db_password"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "database_api_db_password_version" {
  secret      = google_secret_manager_secret.database_api_db_password_secret.id
  secret_data = random_password.database_api_db_password.result
}

# Create Cloud SQL User with the generated password
resource "google_sql_user" "database_api_neuronest_instance_user" {
  instance = google_sql_database_instance.neuronest_instance.name
  name     = var.cloud_run_cloud_sql_username
  password = random_password.database_api_db_password.result
}
