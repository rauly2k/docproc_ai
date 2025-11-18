/**
 * Main Terraform Configuration for DocProc AI
 *
 * This creates all GCP infrastructure needed for the platform:
 * - Cloud Run services (API Gateway + Workers)
 * - Cloud SQL (PostgreSQL with pgvector)
 * - Pub/Sub (topics and subscriptions)
 * - Cloud Storage (buckets)
 * - IAM (service accounts and permissions)
 */

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  backend "gcs" {
    bucket = "docai-terraform-state"
    prefix = "terraform/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "run.googleapis.com",
    "sql-component.googleapis.com",
    "sqladmin.googleapis.com",
    "pubsub.googleapis.com",
    "storage-api.googleapis.com",
    "documentai.googleapis.com",
    "aiplatform.googleapis.com",
    "vision.googleapis.com",
    "secretmanager.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
  ])

  service            = each.value
  disable_on_destroy = false
}

# IAM Module - Service Accounts
module "iam" {
  source = "./modules/iam"

  project_id = var.project_id
  region     = var.region
}

# Cloud Storage Module
module "storage" {
  source = "./modules/storage"

  project_id  = var.project_id
  region      = var.region
  environment = var.environment
}

# Cloud SQL Module - PostgreSQL with pgvector
module "cloud_sql" {
  source = "./modules/cloud_sql"

  project_id       = var.project_id
  region           = var.region
  environment      = var.environment
  database_version = var.database_version
  tier             = var.database_tier
}

# Pub/Sub Module
module "pubsub" {
  source = "./modules/pubsub"

  project_id  = var.project_id
  environment = var.environment

  cloud_run_sa_email = module.iam.cloud_run_sa_email
}

# Cloud Run Module - API Gateway and Workers
module "cloud_run" {
  source = "./modules/cloud_run"

  project_id  = var.project_id
  region      = var.region
  environment = var.environment

  database_connection_name = module.cloud_sql.connection_name
  database_url            = module.cloud_sql.database_url

  gcs_bucket_uploads   = module.storage.uploads_bucket_name
  gcs_bucket_processed = module.storage.processed_bucket_name

  pubsub_topics = module.pubsub.topic_names

  cloud_run_sa_email = module.iam.cloud_run_sa_email

  depends_on = [
    google_project_service.required_apis,
    module.cloud_sql,
    module.storage,
    module.pubsub,
    module.iam
  ]
}

# Monitoring Module
module "monitoring" {
  source = "./modules/monitoring"

  project_id  = var.project_id
  environment = var.environment

  cloud_run_services = module.cloud_run.service_names
}
