"""Google Cloud Storage utilities."""

from datetime import timedelta
from google.cloud import storage
from .config import get_settings

settings = get_settings()


class GCSManager:
    """Manage Google Cloud Storage operations."""

    def __init__(self):
        self.client = storage.Client()

    def get_signed_url(
        self,
        gcs_uri: str,
        expiration_minutes: int = 15
    ) -> str:
        """
        Generate signed URL for downloading a file.

        Args:
            gcs_uri: GCS URI (gs://bucket/path/to/file)
            expiration_minutes: URL expiration time

        Returns:
            Signed URL
        """
        # Parse GCS URI
        parts = gcs_uri.replace("gs://", "").split("/", 1)
        bucket_name = parts[0]
        blob_path = parts[1] if len(parts) > 1 else ""

        # Get bucket and blob
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(blob_path)

        # Generate signed URL
        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=expiration_minutes),
            method="GET"
        )

        return url

    def upload_file(
        self,
        local_path: str,
        bucket_name: str,
        blob_path: str,
        content_type: str = None
    ) -> str:
        """
        Upload file to GCS.

        Args:
            local_path: Path to local file
            bucket_name: GCS bucket name
            blob_path: Path in bucket
            content_type: MIME type

        Returns:
            GCS URI
        """
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(blob_path)

        blob.upload_from_filename(local_path, content_type=content_type)

        return f"gs://{bucket_name}/{blob_path}"

    def download_file(
        self,
        gcs_uri: str,
        local_path: str
    ) -> None:
        """
        Download file from GCS.

        Args:
            gcs_uri: GCS URI
            local_path: Where to save the file
        """
        parts = gcs_uri.replace("gs://", "").split("/", 1)
        bucket_name = parts[0]
        blob_path = parts[1] if len(parts) > 1 else ""

        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(blob_path)

        blob.download_to_filename(local_path)
