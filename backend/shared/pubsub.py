"""Google Cloud Pub/Sub utilities."""

from google.cloud import pubsub_v1
import json
from typing import Dict, Any

"""Google Pub/Sub utilities for async job processing."""

import json
from typing import Dict, Any
from uuid import UUID
from google.cloud import pubsub_v1
from .config import get_settings

settings = get_settings()


class PubSubPublisher:
    """Publish messages to Pub/Sub topics."""

    def __init__(self):
        self.publisher = pubsub_v1.PublisherClient()
        self.project_id = settings.project_id

    def _get_topic_path(self, topic_name: str) -> str:
        """Get full topic path."""
        return self.publisher.topic_path(self.project_id, topic_name)

    def publish_invoice_processing(self, message: Dict[str, Any]) -> str:
        """Publish invoice processing job."""
        topic_path = self._get_topic_path(settings.pubsub_topic_invoice)
        message_bytes = json.dumps(message).encode("utf-8")

        future = self.publisher.publish(topic_path, message_bytes)
        return future.result()

    def publish_ocr_processing(self, message: Dict[str, Any]) -> str:
        """Publish OCR processing job."""
        topic_path = self._get_topic_path(settings.pubsub_topic_ocr)
        message_bytes = json.dumps(message).encode("utf-8")

        future = self.publisher.publish(topic_path, message_bytes)
        return future.result()

    def publish_summarization(self, message: Dict[str, Any]) -> str:
        """Publish summarization job."""
        topic_path = self._get_topic_path(settings.pubsub_topic_summary)
        message_bytes = json.dumps(message).encode("utf-8")

        future = self.publisher.publish(topic_path, message_bytes)
        return future.result()

    def publish_rag_ingestion(self, message: Dict[str, Any]) -> str:
        """Publish RAG ingestion job."""
        topic_path = self._get_topic_path(settings.pubsub_topic_rag_ingest)
        message_bytes = json.dumps(message).encode("utf-8")

        future = self.publisher.publish(topic_path, message_bytes)
        return future.result()

    def publish_document_filling(self, message: Dict[str, Any]) -> str:
        """Publish document filling job."""
        topic_path = self._get_topic_path(settings.pubsub_topic_docfill)
        message_bytes = json.dumps(message).encode("utf-8")

        future = self.publisher.publish(topic_path, message_bytes)
        return future.result()

    def publish_message(self, topic_name: str, message: Dict[str, Any]) -> str:
        """Generic publish method."""
        topic_path = self._get_topic_path(topic_name)
        message_bytes = json.dumps(message).encode("utf-8")

        future = self.publisher.publish(topic_path, message_bytes)
        return future.result()
# Initialize Pub/Sub publisher
_publisher_client = None


def get_publisher_client() -> pubsub_v1.PublisherClient:
    """Get or create Pub/Sub publisher client."""
    global _publisher_client
    if _publisher_client is None:
        _publisher_client = pubsub_v1.PublisherClient()
    return _publisher_client


def publish_message(topic_name: str, message_data: Dict[str, Any]) -> str:
    """
    Publish a message to a Pub/Sub topic.

    Args:
        topic_name: Topic name (without project path)
        message_data: Message payload as dictionary

    Returns:
        Message ID
    """
    publisher = get_publisher_client()

    # Construct full topic path
    topic_path = publisher.topic_path(settings.gcp_project_id, topic_name)

    # Convert message to JSON bytes
    message_bytes = json.dumps(message_data).encode("utf-8")

    # Publish message
    future = publisher.publish(topic_path, message_bytes)

    # Wait for publish to complete and get message ID
    message_id = future.result()

    return message_id


def publish_invoice_processing_job(
    tenant_id: str,
    user_id: str,
    document_id: UUID,
    gcs_path: str,
    options: Dict[str, Any] = None
) -> str:
    """
    Publish an invoice processing job.

    Args:
        tenant_id: Tenant ID
        user_id: User ID
        document_id: Document ID
        gcs_path: GCS path to the document
        options: Additional processing options

    Returns:
        Message ID
    """
    message_data = {
        "tenant_id": tenant_id,
        "user_id": user_id,
        "document_id": str(document_id),
        "gcs_path": gcs_path,
        "document_type": "invoice",
        "options": options or {}
    }

    return publish_message(settings.pubsub_invoice_topic, message_data)


def publish_ocr_processing_job(
    tenant_id: str,
    user_id: str,
    document_id: UUID,
    gcs_path: str,
    ocr_method: str = "document-ai",
    options: Dict[str, Any] = None
) -> str:
    """
    Publish an OCR processing job.

    Args:
        tenant_id: Tenant ID
        user_id: User ID
        document_id: Document ID
        gcs_path: GCS path to the document
        ocr_method: OCR method to use
        options: Additional processing options

    Returns:
        Message ID
    """
    message_data = {
        "tenant_id": tenant_id,
        "user_id": user_id,
        "document_id": str(document_id),
        "gcs_path": gcs_path,
        "document_type": "generic",
        "options": {
            "ocr_method": ocr_method,
            **(options or {})
        }
    }

    return publish_message(settings.pubsub_ocr_topic, message_data)


def publish_summarization_job(
    tenant_id: str,
    user_id: str,
    document_id: UUID,
    gcs_path: str,
    model: str = "gemini-1.5-flash",
    options: Dict[str, Any] = None
) -> str:
    """
    Publish a summarization job.

    Args:
        tenant_id: Tenant ID
        user_id: User ID
        document_id: Document ID
        gcs_path: GCS path to the document
        model: AI model to use
        options: Additional processing options

    Returns:
        Message ID
    """
    message_data = {
        "tenant_id": tenant_id,
        "user_id": user_id,
        "document_id": str(document_id),
        "gcs_path": gcs_path,
        "document_type": "generic",
        "options": {
            "model": model,
            **(options or {})
        }
    }

    return publish_message(settings.pubsub_summarization_topic, message_data)


def publish_rag_ingestion_job(
    tenant_id: str,
    user_id: str,
    document_id: UUID,
    gcs_path: str,
    options: Dict[str, Any] = None
) -> str:
    """
    Publish a RAG ingestion job (for indexing documents for chat).

    Args:
        tenant_id: Tenant ID
        user_id: User ID
        document_id: Document ID
        gcs_path: GCS path to the document
        options: Additional processing options

    Returns:
        Message ID
    """
    message_data = {
        "tenant_id": tenant_id,
        "user_id": user_id,
        "document_id": str(document_id),
        "gcs_path": gcs_path,
        "document_type": "generic",
        "options": options or {}
    }

    return publish_message(settings.pubsub_rag_ingestion_topic, message_data)


def publish_document_filling_job(
    tenant_id: str,
    user_id: str,
    document_id: UUID,
    gcs_path: str,
    template_name: str,
    options: Dict[str, Any] = None
) -> str:
    """
    Publish a document filling job (ID extraction + PDF filling).

    Args:
        tenant_id: Tenant ID
        user_id: User ID
        document_id: Document ID
        gcs_path: GCS path to the ID document
        template_name: PDF template to fill
        options: Additional processing options

    Returns:
        Message ID
    """
    message_data = {
        "tenant_id": tenant_id,
        "user_id": user_id,
        "document_id": str(document_id),
        "gcs_path": gcs_path,
        "document_type": "id_document",
        "options": {
            "template_name": template_name,
            **(options or {})
        }
    }

    return publish_message(settings.pubsub_docfill_topic, message_data)


def publish_processing_complete_event(
    tenant_id: str,
    document_id: UUID,
    processing_type: str,
    status: str,
    details: Dict[str, Any] = None
) -> str:
    """
    Publish a processing completion event (for frontend notifications).

    Args:
        tenant_id: Tenant ID
        document_id: Document ID
        processing_type: Type of processing completed
        status: Processing status (completed, failed)
        details: Additional details

    Returns:
        Message ID
    """
    message_data = {
        "tenant_id": tenant_id,
        "document_id": str(document_id),
        "processing_type": processing_type,
        "status": status,
        "details": details or {}
    }

    return publish_message(settings.pubsub_processing_complete_topic, message_data)
