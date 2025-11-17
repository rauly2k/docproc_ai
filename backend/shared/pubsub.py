"""Google Pub/Sub utilities."""

from google.cloud import pubsub_v1
import json
from typing import Dict, Any

from .config import get_settings

settings = get_settings()


class PubSubPublisher:
    """Publish messages to Pub/Sub topics."""

    def __init__(self):
        self.client = pubsub_v1.PublisherClient()
        self.project_id = settings.project_id

    def _publish(self, topic_name: str, message: Dict[str, Any]) -> str:
        """
        Publish message to topic.

        Args:
            topic_name: Pub/Sub topic name
            message: Message dictionary to publish

        Returns:
            Message ID
        """
        topic_path = self.client.topic_path(self.project_id, topic_name)
        message_json = json.dumps(message)
        message_bytes = message_json.encode("utf-8")

        future = self.client.publish(topic_path, message_bytes)
        message_id = future.result()

        return message_id

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
        return self._publish(settings.pubsub_topic_summary, message)

    def publish_ocr(self, message: Dict[str, Any]) -> str:
        """Publish OCR job."""
        return self._publish(settings.pubsub_topic_ocr, message)

    def publish_invoice(self, message: Dict[str, Any]) -> str:
        """Publish invoice processing job."""
        return self._publish(settings.pubsub_topic_invoice, message)

    def publish_rag_ingest(self, message: Dict[str, Any]) -> str:
        """Publish RAG ingestion job."""
        return self._publish(settings.pubsub_topic_rag_ingest, message)

    def publish_docfill(self, message: Dict[str, Any]) -> str:
        """Publish document filling job."""
        return self._publish(settings.pubsub_topic_docfill, message)
