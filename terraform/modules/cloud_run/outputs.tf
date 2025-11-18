output "api_gateway_url" {
  description = "API Gateway URL"
  value       = google_cloud_run_v2_service.api_gateway.uri
}

output "service_names" {
  description = "All Cloud Run service names"
  value = {
    api_gateway       = google_cloud_run_v2_service.api_gateway.name
    invoice_worker    = google_cloud_run_v2_service.invoice_worker.name
    ocr_worker        = google_cloud_run_v2_service.ocr_worker.name
    summarizer_worker = google_cloud_run_v2_service.summarizer_worker.name
    rag_ingest_worker = google_cloud_run_v2_service.rag_ingest_worker.name
    docfill_worker    = google_cloud_run_v2_service.docfill_worker.name
  }
}

output "worker_urls" {
  description = "Worker service URLs"
  value = {
    invoice_worker    = google_cloud_run_v2_service.invoice_worker.uri
    ocr_worker        = google_cloud_run_v2_service.ocr_worker.uri
    summarizer_worker = google_cloud_run_v2_service.summarizer_worker.uri
    rag_ingest_worker = google_cloud_run_v2_service.rag_ingest_worker.uri
    docfill_worker    = google_cloud_run_v2_service.docfill_worker.uri
  }
}
