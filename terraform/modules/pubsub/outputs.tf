output "topic_names" {
  description = "Pub/Sub topic names"
  value = {
    invoice_processing = google_pubsub_topic.topics["invoice_processing"].name
    ocr_processing     = google_pubsub_topic.topics["ocr_processing"].name
    summarization      = google_pubsub_topic.topics["summarization"].name
    rag_ingestion      = google_pubsub_topic.topics["rag_ingestion"].name
    document_filling   = google_pubsub_topic.topics["document_filling"].name
  }
}

output "subscription_names" {
  description = "Pub/Sub subscription names"
  value = {
    invoice_worker    = google_pubsub_subscription.invoice_worker.name
    ocr_worker        = google_pubsub_subscription.ocr_worker.name
    summarizer_worker = google_pubsub_subscription.summarizer_worker.name
    rag_ingest_worker = google_pubsub_subscription.rag_ingest_worker.name
    docfill_worker    = google_pubsub_subscription.docfill_worker.name
  }
}
