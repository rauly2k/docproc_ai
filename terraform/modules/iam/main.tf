# IAM Module - Service Accounts and Permissions

resource "google_service_account" "cloud_run" {
  account_id   = "docai-cloud-run-${var.environment}"
  display_name = "Cloud Run Service Account for DocProc AI"
  description  = "Service account used by Cloud Run services (API Gateway and Workers)"
}

# Grant Cloud Run service account access to Cloud SQL
resource "google_project_iam_member" "cloud_sql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.cloud_run.email}"
}

# Grant access to Cloud Storage
resource "google_project_iam_member" "storage_admin" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.cloud_run.email}"
}

# Grant access to Pub/Sub
resource "google_project_iam_member" "pubsub_publisher" {
  project = var.project_id
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${google_service_account.cloud_run.email}"
}

resource "google_project_iam_member" "pubsub_subscriber" {
  project = var.project_id
  role    = "roles/pubsub.subscriber"
  member  = "serviceAccount:${google_service_account.cloud_run.email}"
}

# Grant access to Document AI
resource "google_project_iam_member" "documentai_user" {
  project = var.project_id
  role    = "roles/documentai.apiUser"
  member  = "serviceAccount:${google_service_account.cloud_run.email}"
}

# Grant access to Vertex AI
resource "google_project_iam_member" "aiplatform_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.cloud_run.email}"
}

# Grant access to Secret Manager
resource "google_project_iam_member" "secretmanager_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.cloud_run.email}"
}

# Grant access to Vision API
resource "google_project_iam_member" "vision_user" {
  project = var.project_id
  role    = "roles/cloudvision.user"
  member  = "serviceAccount:${google_service_account.cloud_run.email}"
}
