##############################################
#       Cloud SQL PostgreSQL Instance        #
##############################################

# Cloud SQL Instance for PostgreSQL 12
resource "google_sql_database_instance" "neuronest_instance" {
  provider         = google-beta
  name             = var.cloud_sql_instance_name
  database_version = "POSTGRES_12"
  region           = var.region
  settings {
    tier = "db-f1-micro" # Default minimal settings
    backup_configuration {
      enabled = true
    }
    ip_configuration {
      ipv4_enabled = true
    }
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
