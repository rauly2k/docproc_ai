# Pub/Sub Module - Topics and Subscriptions

locals {
  topics = {
    invoice_processing = "docai-invoice-processing-${var.environment}"
    ocr_processing     = "docai-ocr-processing-${var.environment}"
    summarization      = "docai-summarization-${var.environment}"
    rag_ingestion      = "docai-rag-ingestion-${var.environment}"
    document_filling   = "docai-document-filling-${var.environment}"
  }
}

# Create Pub/Sub topics
resource "google_pubsub_topic" "topics" {
  for_each = local.topics

  name    = each.value
  project = var.project_id

  message_retention_duration = "86400s" # 24 hours
}

# Create subscriptions for each worker
resource "google_pubsub_subscription" "invoice_worker" {
  name    = "docai-invoice-worker-sub-${var.environment}"
  topic   = google_pubsub_topic.topics["invoice_processing"].name
  project = var.project_id

  ack_deadline_seconds = 60

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }

  expiration_policy {
    ttl = "" # Never expire
  }
}

resource "google_pubsub_subscription" "ocr_worker" {
  name    = "docai-ocr-worker-sub-${var.environment}"
  topic   = google_pubsub_topic.topics["ocr_processing"].name
  project = var.project_id

  ack_deadline_seconds = 60

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }

  expiration_policy {
    ttl = ""
  }
}

resource "google_pubsub_subscription" "summarizer_worker" {
  name    = "docai-summarizer-worker-sub-${var.environment}"
  topic   = google_pubsub_topic.topics["summarization"].name
  project = var.project_id

  ack_deadline_seconds = 120 # Longer for AI processing

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }

  expiration_policy {
    ttl = ""
  }
}

resource "google_pubsub_subscription" "rag_ingest_worker" {
  name    = "docai-rag-ingest-worker-sub-${var.environment}"
  topic   = google_pubsub_topic.topics["rag_ingestion"].name
  project = var.project_id

  ack_deadline_seconds = 300 # 5 minutes for large documents

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }

  expiration_policy {
    ttl = ""
  }
}

resource "google_pubsub_subscription" "docfill_worker" {
  name    = "docai-docfill-worker-sub-${var.environment}"
  topic   = google_pubsub_topic.topics["document_filling"].name
  project = var.project_id

  ack_deadline_seconds = 60

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }

  expiration_policy {
    ttl = ""
  }
}

# Grant publisher permissions to Cloud Run service account
resource "google_pubsub_topic_iam_member" "publisher" {
  for_each = google_pubsub_topic.topics

  project = var.project_id
  topic   = each.value.name
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${var.cloud_run_sa_email}"
}

# Grant subscriber permissions
resource "google_pubsub_subscription_iam_member" "subscriber" {
  for_each = {
    invoice    = google_pubsub_subscription.invoice_worker.name
    ocr        = google_pubsub_subscription.ocr_worker.name
    summarizer = google_pubsub_subscription.summarizer_worker.name
    rag_ingest = google_pubsub_subscription.rag_ingest_worker.name
    docfill    = google_pubsub_subscription.docfill_worker.name
  }

  project      = var.project_id
  subscription = each.value
  role         = "roles/pubsub.subscriber"
  member       = "serviceAccount:${var.cloud_run_sa_email}"
}
