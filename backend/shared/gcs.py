"""Google Cloud Storage utilities."""

from google.cloud import storage
from typing import BinaryIO
import uuid
from datetime import datetime, timedelta

import os
from typing import Optional, BinaryIO
from uuid import UUID
from google.cloud import storage
from google.cloud.exceptions import NotFound
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
# Initialize GCS client
_storage_client = None


def get_storage_client() -> storage.Client:
    """Get or create GCS client."""
    global _storage_client
    if _storage_client is None:
        _storage_client = storage.Client(project=settings.gcp_project_id)
    return _storage_client


def upload_file_to_gcs(
    file_data: BinaryIO,
    tenant_id: str,
    document_id: UUID,
    filename: str,
    bucket_name: Optional[str] = None,
    content_type: Optional[str] = None
) -> str:
    """
    Upload a file to Google Cloud Storage.

    Args:
        file_data: File binary data
        tenant_id: Tenant ID for path isolation
        document_id: Document ID
        filename: Original filename
        bucket_name: GCS bucket name (defaults to uploads bucket)
        content_type: MIME type of the file

    Returns:
        GCS path (gs://bucket/path/to/file)
    """
    if bucket_name is None:
        bucket_name = settings.gcs_uploads_bucket

    client = get_storage_client()
    bucket = client.bucket(bucket_name)

    # Construct GCS path: {tenant_id}/{document_id}/{filename}
    blob_path = f"{tenant_id}/{document_id}/{filename}"
    blob = bucket.blob(blob_path)

    # Set content type if provided
    if content_type:
        blob.content_type = content_type

    # Upload file
    blob.upload_from_file(file_data, rewind=True)

    # Return GCS URI
    return f"gs://{bucket_name}/{blob_path}"


def download_file_from_gcs(gcs_path: str) -> bytes:
    """
    Download a file from Google Cloud Storage.

    Args:
        gcs_path: GCS path (gs://bucket/path/to/file)

    Returns:
        File contents as bytes

    Raises:
        NotFound: If file doesn't exist
    """
    # Parse GCS path
    if not gcs_path.startswith("gs://"):
        raise ValueError(f"Invalid GCS path: {gcs_path}")

    path_parts = gcs_path[5:].split("/", 1)
    bucket_name = path_parts[0]
    blob_path = path_parts[1]

    client = get_storage_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_path)

    # Download file
    return blob.download_as_bytes()


def delete_file_from_gcs(gcs_path: str) -> bool:
    """
    Delete a file from Google Cloud Storage.

    Args:
        gcs_path: GCS path (gs://bucket/path/to/file)

    Returns:
        True if deleted, False if not found
    """
    try:
        # Parse GCS path
        if not gcs_path.startswith("gs://"):
            raise ValueError(f"Invalid GCS path: {gcs_path}")

        path_parts = gcs_path[5:].split("/", 1)
        bucket_name = path_parts[0]
        blob_path = path_parts[1]

        client = get_storage_client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_path)

        blob.delete()
        return True
    except NotFound:
        return False


def generate_signed_url(gcs_path: str, expiration_minutes: int = 60) -> str:
    """
    Generate a signed URL for temporary access to a GCS file.

    Args:
        gcs_path: GCS path (gs://bucket/path/to/file)
        expiration_minutes: URL expiration time in minutes

    Returns:
        Signed URL
    """
    # Parse GCS path
    if not gcs_path.startswith("gs://"):
        raise ValueError(f"Invalid GCS path: {gcs_path}")

    path_parts = gcs_path[5:].split("/", 1)
    bucket_name = path_parts[0]
    blob_path = path_parts[1]

    client = get_storage_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_path)

    # Generate signed URL
    url = blob.generate_signed_url(
        version="v4",
        expiration=expiration_minutes * 60,  # Convert to seconds
        method="GET"
    )

    return url


def file_exists_in_gcs(gcs_path: str) -> bool:
    """
    Check if a file exists in Google Cloud Storage.

    Args:
        gcs_path: GCS path (gs://bucket/path/to/file)

    Returns:
        True if file exists, False otherwise
    """
    try:
        # Parse GCS path
        if not gcs_path.startswith("gs://"):
            return False

        path_parts = gcs_path[5:].split("/", 1)
        if len(path_parts) < 2:
            return False

        bucket_name = path_parts[0]
        blob_path = path_parts[1]

        client = get_storage_client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_path)

        return blob.exists()
    except Exception:
        return False


def get_file_size(gcs_path: str) -> Optional[int]:
    """
    Get file size in bytes.

    Args:
        gcs_path: GCS path (gs://bucket/path/to/file)

    Returns:
        File size in bytes or None if file doesn't exist
    """
    try:
        # Parse GCS path
        if not gcs_path.startswith("gs://"):
            return None

        path_parts = gcs_path[5:].split("/", 1)
        bucket_name = path_parts[0]
        blob_path = path_parts[1]

        client = get_storage_client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_path)

        blob.reload()  # Fetch metadata
        return blob.size
    except Exception:
        return None
