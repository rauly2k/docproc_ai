"""Google Pub/Sub utilities."""

from google.cloud import pubsub_v1
import json
from typing import Dict, Any

from .config import get_settings

settings = get_settings()


class PubSubPublisher:
    """Publish messages to Google Pub/Sub topics."""

    def __init__(self):
        self.client = pubsub_v1.PublisherClient()
        self.project_id = settings.project_id

    def _publish_message(self, topic_name: str, message: Dict[str, Any]) -> str:
        """
        Publish a message to a Pub/Sub topic.

        Args:
            topic_name: Name of the topic
            message: Message data as dictionary

        Returns:
            Message ID
        """
        topic_path = self.client.topic_path(self.project_id, topic_name)

        # Convert message to JSON bytes
        message_json = json.dumps(message)
        message_bytes = message_json.encode("utf-8")

        # Publish message
        future = self.client.publish(topic_path, message_bytes)
        message_id = future.result()

        return message_id

    def publish_invoice_processing(self, message: Dict[str, Any]) -> str:
        """Publish invoice processing job."""
        return self._publish_message(settings.pubsub_topic_invoice, message)

    def publish_ocr_processing(self, message: Dict[str, Any]) -> str:
        """Publish OCR processing job."""
        return self._publish_message(settings.pubsub_topic_ocr, message)

    def publish_summarization_processing(self, message: Dict[str, Any]) -> str:
        """Publish summarization processing job."""
        return self._publish_message(settings.pubsub_topic_summarization, message)

    def publish_rag_ingestion(self, message: Dict[str, Any]) -> str:
        """Publish RAG ingestion job."""
        return self._publish_message(settings.pubsub_topic_rag_ingest, message)

    def publish_rag_query(self, message: Dict[str, Any]) -> str:
        """Publish RAG query job."""
        return self._publish_message(settings.pubsub_topic_rag_query, message)

    def publish_document_filling(self, message: Dict[str, Any]) -> str:
        """Publish document filling job."""
        return self._publish_message(settings.pubsub_topic_docfill, message)
