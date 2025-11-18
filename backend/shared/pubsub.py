"""Google Cloud Pub/Sub utilities for async job processing."""

import json
from typing import Dict, Any
from google.cloud import pubsub_v1

from .config import get_settings

settings = get_settings()


class PubSubPublisher:
    """Publish messages to Google Pub/Sub topics."""

    def __init__(self):
        self.client = pubsub_v1.PublisherClient()
        self.project_id = settings.project_id

    def _get_topic_path(self, topic_name: str) -> str:
        """Get full topic path."""
        return self.client.topic_path(self.project_id, topic_name)

    def _publish_message(self, topic_name: str, message: Dict[str, Any]) -> str:
        """
        Generic publish method.

        Args:
            topic_name: Pub/Sub topic name
            message: Message data dictionary

        Returns:
            Message ID

        Raises:
            Exception: If publishing fails
        """
        topic_path = self._get_topic_path(topic_name)

        # Convert message to JSON bytes
        message_json = json.dumps(message)
        message_bytes = message_json.encode("utf-8")

        # Publish message
        try:
            future = self.client.publish(topic_path, message_bytes)
            message_id = future.result()
            return message_id
        except Exception as e:
            print(f"Error publishing to {topic_name}: {e}")
            raise

    def publish_invoice_processing(self, message: Dict[str, Any]) -> str:
        """
        Publish invoice processing job.

        Expected message format:
        {
            "tenant_id": "uuid",
            "user_id": "uuid",
            "document_id": "uuid",
            "gcs_path": "gs://bucket/path",
            "document_type": "invoice"
        }
        """
        return self._publish_message(settings.pubsub_topic_invoice, message)

    def publish_ocr_processing(self, message: Dict[str, Any]) -> str:
        """
        Publish OCR processing job.

        Expected message format:
        {
            "tenant_id": "uuid",
            "user_id": "uuid",
            "document_id": "uuid",
            "gcs_path": "gs://bucket/path",
            "options": {"ocr_method": "document-ai|vision|gemini"}
        }
        """
        return self._publish_message(settings.pubsub_topic_ocr, message)

    def publish_summarization(self, message: Dict[str, Any]) -> str:
        """
        Publish summarization job.

        Expected message format:
        {
            "tenant_id": "uuid",
            "user_id": "uuid",
            "document_id": "uuid",
            "gcs_path": "gs://bucket/path",
            "model_preference": "flash|pro|auto",
            "summary_type": "concise|detailed"
        }
        """
        return self._publish_message(settings.pubsub_topic_summary, message)

    def publish_rag_ingestion(self, message: Dict[str, Any]) -> str:
        """
        Publish RAG ingestion job (for indexing documents for chat).

        Expected message format:
        {
            "tenant_id": "uuid",
            "user_id": "uuid",
            "document_id": "uuid",
            "gcs_path": "gs://bucket/path"
        }
        """
        return self._publish_message(settings.pubsub_topic_rag_ingest, message)

    def publish_document_filling(self, message: Dict[str, Any]) -> str:
        """
        Publish document filling job (ID extraction + PDF filling).

        Expected message format:
        {
            "tenant_id": "uuid",
            "user_id": "uuid",
            "document_id": "uuid",
            "gcs_path": "gs://bucket/path",
            "template_name": "template_name"
        }
        """
        return self._publish_message(settings.pubsub_topic_docfill, message)

    def publish_message(self, topic_name: str, message: Dict[str, Any]) -> str:
        """
        Generic publish method for any topic.

        Args:
            topic_name: Topic name to publish to
            message: Message data dictionary

        Returns:
            Message ID
        """
        return self._publish_message(topic_name, message)
