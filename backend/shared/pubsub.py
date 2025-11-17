"""Google Pub/Sub utilities."""

import json
from google.cloud import pubsub_v1
from .config import get_settings

settings = get_settings()


class PubSubPublisher:
    """Publish messages to Pub/Sub topics."""

    def __init__(self):
        self.publisher = pubsub_v1.PublisherClient()
        self.project_id = settings.project_id

    def _publish_message(self, topic_name: str, message: dict) -> str:
        """
        Publish a message to a topic.

        Args:
            topic_name: Name of the topic
            message: Message data (will be JSON encoded)

        Returns:
            Message ID
        """
        topic_path = self.publisher.topic_path(self.project_id, topic_name)

        # Encode message as JSON bytes
        message_bytes = json.dumps(message).encode("utf-8")

        # Publish
        future = self.publisher.publish(topic_path, message_bytes)
        message_id = future.result()

        return message_id

    def publish_invoice_processing(self, message: dict) -> str:
        """Publish invoice processing job."""
        return self._publish_message(settings.pubsub_invoice_topic, message)

    def publish_ocr_processing(self, message: dict) -> str:
        """Publish OCR processing job."""
        return self._publish_message(settings.pubsub_ocr_topic, message)

    def publish_summarization(self, message: dict) -> str:
        """Publish summarization job."""
        return self._publish_message(settings.pubsub_summarization_topic, message)

    def publish_rag_ingestion(self, message: dict) -> str:
        """Publish RAG ingestion job."""
        return self._publish_message(settings.pubsub_rag_ingestion_topic, message)

    def publish_rag_query(self, message: dict) -> str:
        """Publish RAG query job."""
        return self._publish_message(settings.pubsub_rag_query_topic, message)

    def publish_document_filling(self, message: dict) -> str:
        """Publish document filling job."""
        return self._publish_message(settings.pubsub_document_filling_topic, message)
