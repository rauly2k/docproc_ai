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


# Global instance
pubsub_publisher = PubSubPublisher()
