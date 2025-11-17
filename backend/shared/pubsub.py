"""Google Cloud Pub/Sub utilities."""

from google.cloud import pubsub_v1
import json
from typing import Dict, Any

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

    def _publish(self, topic_name: str, message: Dict[str, Any]) -> str:
        """
        Generic publish method.

        Args:
            topic_name: Pub/Sub topic name
            message: Message data dictionary

        Returns:
            Message ID
        """
        topic_path = self._get_topic_path(topic_name)
        message_bytes = json.dumps(message).encode("utf-8")

        try:
            future = self.publisher.publish(topic_path, message_bytes)
            message_id = future.result()
            return message_id
        except Exception as e:
            print(f"Error publishing to {topic_name}: {e}")
            raise

    def publish_invoice_processing(self, message: Dict[str, Any]) -> str:
        """Publish invoice processing job."""
        return self._publish(settings.pubsub_topic_invoice, message)

    def publish_ocr_processing(self, message: Dict[str, Any]) -> str:
        """Publish OCR processing job."""
        return self._publish(settings.pubsub_topic_ocr, message)

    def publish_summarization(self, message: Dict[str, Any]) -> str:
        """Publish summarization job."""
        return self._publish(settings.pubsub_topic_summary, message)

    def publish_rag_ingestion(self, message: Dict[str, Any]) -> str:
        """Publish RAG ingestion job."""
        return self._publish(settings.pubsub_topic_rag_ingest, message)

    def publish_document_filling(self, message: Dict[str, Any]) -> str:
        """Publish document filling job."""
        return self._publish(settings.pubsub_topic_docfill, message)

    def publish_message(self, topic_name: str, message: Dict[str, Any]) -> str:
        """Generic publish method for any topic."""
        return self._publish(topic_name, message)
