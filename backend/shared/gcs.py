"""Google Cloud Storage utilities."""

from google.cloud import storage
from google.cloud.exceptions import NotFound
from typing import BinaryIO, Optional
from datetime import timedelta

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
        Upload document to GCS uploads bucket.

        Args:
            file: File object to upload
            tenant_id: Tenant UUID
            document_id: Document UUID
            filename: Original filename
            content_type: MIME type

        Returns:
            GCS URI (gs://bucket/path)
        """
        # Generate blob path: {tenant_id}/{document_id}/filename
        blob_name = f"{tenant_id}/{document_id}/{filename}"
        blob = self.bucket_uploads.blob(blob_name)

        # Upload with metadata
        blob.metadata = {
            "tenant_id": tenant_id,
            "document_id": document_id,
        }

        blob.upload_from_file(file, content_type=content_type, rewind=True)

        # Return GCS URI
        return f"gs://{self.bucket_uploads.name}/{blob_name}"

    def download_document(self, gcs_uri: str) -> bytes:
        """
        Download document from GCS.

        Args:
            gcs_uri: GCS URI (gs://bucket/path)

        Returns:
            File contents as bytes

        Raises:
            NotFound: If file doesn't exist
        """
        # Parse GCS URI: gs://bucket/path
        if not gcs_uri.startswith("gs://"):
            raise ValueError(f"Invalid GCS URI: {gcs_uri}")

        path_parts = gcs_uri[5:].split("/", 1)
        bucket_name = path_parts[0]
        blob_path = path_parts[1]

        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(blob_path)

        return blob.download_as_bytes()

    def get_signed_url(self, gcs_uri: str, expiration_minutes: int = 15) -> str:
        """
        Generate signed URL for temporary access.

        Args:
            gcs_uri: GCS URI (gs://bucket/path)
            expiration_minutes: URL expiration time in minutes

        Returns:
            Signed URL string

        Raises:
            ValueError: If GCS URI is invalid
        """
        # Parse GCS URI
        if not gcs_uri.startswith("gs://"):
            raise ValueError(f"Invalid GCS URI: {gcs_uri}")

        path_parts = gcs_uri[5:].split("/", 1)
        bucket_name = path_parts[0]
        blob_path = path_parts[1]

        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(blob_path)

        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=expiration_minutes),
            method="GET",
        )

        return url

    def delete_document(self, gcs_uri: str) -> bool:
        """
        Delete document from GCS.

        Args:
            gcs_uri: GCS URI (gs://bucket/path)

        Returns:
            True if deleted, False if not found
        """
        try:
            # Parse GCS URI
            if not gcs_uri.startswith("gs://"):
                raise ValueError(f"Invalid GCS URI: {gcs_uri}")

            path_parts = gcs_uri[5:].split("/", 1)
            bucket_name = path_parts[0]
            blob_path = path_parts[1]

            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(blob_path)
            blob.delete()
            return True
        except NotFound:
            return False

    def file_exists(self, gcs_uri: str) -> bool:
        """
        Check if file exists in GCS.

        Args:
            gcs_uri: GCS URI (gs://bucket/path)

        Returns:
            True if file exists, False otherwise
        """
        try:
            # Parse GCS URI
            if not gcs_uri.startswith("gs://"):
                return False

            path_parts = gcs_uri[5:].split("/", 1)
            if len(path_parts) < 2:
                return False

            bucket_name = path_parts[0]
            blob_path = path_parts[1]

            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(blob_path)

            return blob.exists()
        except Exception:
            return False

    def get_file_size(self, gcs_uri: str) -> Optional[int]:
        """
        Get file size in bytes.

        Args:
            gcs_uri: GCS URI (gs://bucket/path)

        Returns:
            File size in bytes or None if file doesn't exist
        """
        try:
            # Parse GCS URI
            if not gcs_uri.startswith("gs://"):
                return None

            path_parts = gcs_uri[5:].split("/", 1)
            bucket_name = path_parts[0]
            blob_path = path_parts[1]

            bucket = self.client.bucket(bucket_name)
            blob = bucket.blob(blob_path)

            blob.reload()  # Fetch metadata
            return blob.size
        except Exception:
            return None
