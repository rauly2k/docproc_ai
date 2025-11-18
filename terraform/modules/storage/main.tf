# Cloud Storage Module

# Bucket for uploaded documents
resource "google_storage_bucket" "uploads" {
  name          = "docai-uploads-${var.environment}"
  location      = var.region
  project       = var.project_id
  force_destroy = var.environment != "prod"

  uniform_bucket_level_access = true

  versioning {
    enabled = var.environment == "prod"
  }

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }

  cors {
    origin          = ["*"]
    method          = ["GET", "HEAD", "PUT", "POST", "DELETE"]
    response_header = ["*"]
    max_age_seconds = 3600
  }
}

# Bucket for processed documents
resource "google_storage_bucket" "processed" {
  name          = "docai-processed-${var.environment}"
  location      = var.region
  project       = var.project_id
  force_destroy = var.environment != "prod"

  uniform_bucket_level_access = true

  versioning {
    enabled = var.environment == "prod"
  }

  lifecycle_rule {
    condition {
      age = 180
    }
    action {
      type = "Delete"
    }
  }
}

# Bucket for embeddings/vectors (optional backups)
resource "google_storage_bucket" "embeddings" {
  name          = "docai-embeddings-${var.environment}"
  location      = var.region
  project       = var.project_id
  force_destroy = var.environment != "prod"

  uniform_bucket_level_access = true
}
