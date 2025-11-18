# Cloud SQL Module - PostgreSQL with pgvector

# Random password for database
resource "random_password" "db_password" {
  length  = 32
  special = true
}

# Store password in Secret Manager
resource "google_secret_manager_secret" "db_password" {
  secret_id = "docai-db-password-${var.environment}"
  project   = var.project_id

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "db_password" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = random_password.db_password.result
}

# Cloud SQL Instance
resource "google_sql_database_instance" "main" {
  name             = "docai-db-${var.environment}"
  database_version = var.database_version
  region           = var.region
  project          = var.project_id

  deletion_protection = var.environment == "prod"

  settings {
    tier = var.tier

    database_flags {
      name  = "cloudsql.iam_authentication"
      value = "on"
    }

    # Enable pgvector extension
    database_flags {
      name  = "cloudsql.enable_pgvector"
      value = "on"
    }

    database_flags {
      name  = "max_connections"
      value = "100"
    }

    backup_configuration {
      enabled                        = var.environment == "prod"
      start_time                     = "03:00"
      point_in_time_recovery_enabled = var.environment == "prod"
      transaction_log_retention_days = 7

      backup_retention_settings {
        retained_backups = 7
      }
    }

    ip_configuration {
      ipv4_enabled    = true
      private_network = null

      authorized_networks {
        name  = "all"
        value = "0.0.0.0/0"
      }
    }

    insights_config {
      query_insights_enabled  = true
      query_plans_per_minute  = 5
      query_string_length     = 1024
      record_application_tags = true
    }
  }
}

# Database
resource "google_sql_database" "main" {
  name     = "docai"
  instance = google_sql_database_instance.main.name
  project  = var.project_id
}

# Database user
resource "google_sql_user" "main" {
  name     = "docai_user"
  instance = google_sql_database_instance.main.name
  password = random_password.db_password.result
  project  = var.project_id
}
