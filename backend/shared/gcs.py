"""Google Cloud Storage utilities."""

from google.cloud import storage
from typing import BinaryIO
import uuid
from datetime import datetime, timedelta

from .config import get_settings

settings = get_settings()


class GCSManager:
    """Manage Google Cloud Storage operations."""

    def __init__(self):
        self.client = storage.Client(project=settings.project_id)
        self.bucket_uploads = self.client.bucket(settings.gcs_bucket_uploads)
        self.bucket_processed = self.client.bucket(settings.gcs_bucket_processed)
        self.bucket_temp = self.client.bucket(settings.gcs_bucket_temp)

    def upload_document(
        self,
        file: BinaryIO,
        tenant_id: str,
        document_id: str,
        filename: str,
        content_type: str = "application/pdf"
    ) -> str:
        """
        Upload document to GCS.

        Args:
            file: File object to upload
            tenant_id: Tenant UUID
            document_id: Document UUID
            filename: Original filename
            content_type: MIME type

        Returns:
            GCS URI (gs://bucket/path)
        """
        # Generate blob path: {tenant_id}/{document_id}/original.pdf
        blob_name = f"{tenant_id}/{document_id}/{filename}"
        blob = self.bucket_uploads.blob(blob_name)

        # Upload with metadata
        blob.metadata = {
            "tenant_id": tenant_id,
            "document_id": document_id,
            "uploaded_at": datetime.utcnow().isoformat(),
        }

        blob.upload_from_file(file, content_type=content_type)

        # Return GCS URI
        return f"gs://{self.bucket_uploads.name}/{blob_name}"

    def download_document(self, gcs_uri: str) -> bytes:
        """Download document from GCS."""
        # Parse GCS URI: gs://bucket/path
        bucket_name = gcs_uri.split("/")[2]
        blob_path = "/".join(gcs_uri.split("/")[3:])

        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(blob_path)

        return blob.download_as_bytes()

    def get_signed_url(self, gcs_uri: str, expiration_minutes: int = 15) -> str:
        """Generate signed URL for temporary access."""
        bucket_name = gcs_uri.split("/")[2]
        blob_path = "/".join(gcs_uri.split("/")[3:])

        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(blob_path)

        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=expiration_minutes),
            method="GET",
        )

        return url

    def delete_document(self, gcs_uri: str):
        """Delete document from GCS."""
        bucket_name = gcs_uri.split("/")[2]
        blob_path = "/".join(gcs_uri.split("/")[3:])

        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(blob_path)
        blob.delete()
