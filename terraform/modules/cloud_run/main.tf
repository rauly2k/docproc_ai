# Cloud Run Module - API Gateway and Worker Services

locals {
  common_env_vars = [
    {
      name  = "PROJECT_ID"
      value = var.project_id
    },
    {
      name  = "REGION"
      value = var.region
    },
    {
      name  = "ENVIRONMENT"
      value = var.environment
    },
    {
      name  = "GCS_BUCKET_UPLOADS"
      value = var.gcs_bucket_uploads
    },
    {
      name  = "GCS_BUCKET_PROCESSED"
      value = var.gcs_bucket_processed
    },
  ]

  database_env_vars = [
    {
      name  = "DATABASE_URL"
      value = var.database_url
    },
    {
      name  = "DB_POOL_SIZE"
      value = "5"
    },
    {
      name  = "DB_MAX_OVERFLOW"
      value = "10"
    },
  ]
}

# API Gateway Service
resource "google_cloud_run_v2_service" "api_gateway" {
  name     = "docai-api-gateway-${var.environment}"
  location = var.region
  project  = var.project_id

  template {
    service_account = var.cloud_run_sa_email

    scaling {
      min_instance_count = var.environment == "prod" ? 1 : 0
      max_instance_count = 10
    }

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/docai-images/api-gateway:latest"

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }

      dynamic "env" {
        for_each = concat(local.common_env_vars, local.database_env_vars)
        content {
          name  = env.value.name
          value = env.value.value
        }
      }

      env {
        name  = "PUBSUB_TOPIC_INVOICE"
        value = var.pubsub_topics.invoice_processing
      }

      env {
        name  = "PUBSUB_TOPIC_OCR"
        value = var.pubsub_topics.ocr_processing
      }

      env {
        name  = "PUBSUB_TOPIC_SUMMARIZATION"
        value = var.pubsub_topics.summarization
      }

      env {
        name  = "PUBSUB_TOPIC_RAG_INGESTION"
        value = var.pubsub_topics.rag_ingestion
      }

      env {
        name  = "PUBSUB_TOPIC_DOCUMENT_FILLING"
        value = var.pubsub_topics.document_filling
      }
    }

    vpc_access {
      egress = "PRIVATE_RANGES_ONLY"
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

# Make API Gateway publicly accessible
resource "google_cloud_run_v2_service_iam_member" "api_gateway_public" {
  project  = google_cloud_run_v2_service.api_gateway.project
  location = google_cloud_run_v2_service.api_gateway.location
  name     = google_cloud_run_v2_service.api_gateway.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Invoice Worker Service
resource "google_cloud_run_v2_service" "invoice_worker" {
  name     = "docai-invoice-worker-${var.environment}"
  location = var.region
  project  = var.project_id

  template {
    service_account = var.cloud_run_sa_email

    scaling {
      min_instance_count = 0
      max_instance_count = 5
    }

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/docai-images/invoice-worker:latest"

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }

      dynamic "env" {
        for_each = concat(local.common_env_vars, local.database_env_vars)
        content {
          name  = env.value.name
          value = env.value.value
        }
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

# OCR Worker Service
resource "google_cloud_run_v2_service" "ocr_worker" {
  name     = "docai-ocr-worker-${var.environment}"
  location = var.region
  project  = var.project_id

  template {
    service_account = var.cloud_run_sa_email

    scaling {
      min_instance_count = 0
      max_instance_count = 5
    }

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/docai-images/ocr-worker:latest"

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }

      dynamic "env" {
        for_each = concat(local.common_env_vars, local.database_env_vars)
        content {
          name  = env.value.name
          value = env.value.value
        }
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

# Summarizer Worker Service
resource "google_cloud_run_v2_service" "summarizer_worker" {
  name     = "docai-summarizer-worker-${var.environment}"
  location = var.region
  project  = var.project_id

  template {
    service_account = var.cloud_run_sa_email

    scaling {
      min_instance_count = 0
      max_instance_count = 5
    }

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/docai-images/summarizer-worker:latest"

      resources {
        limits = {
          cpu    = "1"
          memory = "1Gi"
        }
      }

      dynamic "env" {
        for_each = concat(local.common_env_vars, local.database_env_vars)
        content {
          name  = env.value.name
          value = env.value.value
        }
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

# RAG Ingest Worker Service
resource "google_cloud_run_v2_service" "rag_ingest_worker" {
  name     = "docai-rag-ingest-worker-${var.environment}"
  location = var.region
  project  = var.project_id

  template {
    service_account = var.cloud_run_sa_email

    scaling {
      min_instance_count = 0
      max_instance_count = 5
    }

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/docai-images/rag-ingest-worker:latest"

      resources {
        limits = {
          cpu    = "1"
          memory = "1Gi"
        }
      }

      dynamic "env" {
        for_each = concat(local.common_env_vars, local.database_env_vars)
        content {
          name  = env.value.name
          value = env.value.value
        }
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

# Document Filling Worker Service
resource "google_cloud_run_v2_service" "docfill_worker" {
  name     = "docai-docfill-worker-${var.environment}"
  location = var.region
  project  = var.project_id

  template {
    service_account = var.cloud_run_sa_email

    scaling {
      min_instance_count = 0
      max_instance_count = 5
    }

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/docai-images/docfill-worker:latest"

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }

      dynamic "env" {
        for_each = concat(local.common_env_vars, local.database_env_vars)
        content {
          name  = env.value.name
          value = env.value.value
        }
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}
