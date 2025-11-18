"""Structured logging for Cloud Logging integration."""

import logging
import json
from typing import Any, Dict, Optional
from datetime import datetime
from contextvars import ContextVar
import traceback
import os

# Context variables for request tracing
request_id_var: ContextVar[str] = ContextVar('request_id', default='')
tenant_id_var: ContextVar[str] = ContextVar('tenant_id', default='')
user_id_var: ContextVar[str] = ContextVar('user_id', default='')

# Check if running in GCP
IS_GCP = os.getenv('K_SERVICE') is not None

if IS_GCP:
    try:
        from google.cloud import logging as cloud_logging
        cloud_client = cloud_logging.Client()
    except Exception:
        cloud_client = None
else:
    cloud_client = None


class StructuredLogger:
    """Google Cloud Logging compatible structured logger."""

    def __init__(self, service_name: str):
        self.service_name = service_name

        # Setup Python logging for local development
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.local_logger = logging.getLogger(service_name)

        # Setup Cloud Logging if available
        if cloud_client:
            self.cloud_logger = cloud_client.logger(service_name)
        else:
            self.cloud_logger = None

    def _build_log_entry(
        self,
        level: str,
        message: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Build structured log entry."""
        entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'severity': level,
            'message': message,
            'service': self.service_name,
            'request_id': request_id_var.get() or None,
            'tenant_id': tenant_id_var.get() or None,
            'user_id': user_id_var.get() or None,
        }

        # Remove None values
        entry = {k: v for k, v in entry.items() if v is not None}

        # Add any additional fields
        entry.update(kwargs)

        return entry

    def info(self, message: str, **kwargs):
        """Log info level message."""
        entry = self._build_log_entry('INFO', message, **kwargs)

        if self.cloud_logger:
            self.cloud_logger.log_struct(entry, severity='INFO')

        self.local_logger.info(json.dumps(entry))

    def error(
        self,
        message: str,
        error: Optional[Exception] = None,
        **kwargs
    ):
        """Log error level message."""
        entry = self._build_log_entry('ERROR', message, **kwargs)

        if error:
            entry['error'] = {
                'type': type(error).__name__,
                'message': str(error),
                'traceback': self._get_traceback(error)
            }

        if self.cloud_logger:
            self.cloud_logger.log_struct(entry, severity='ERROR')

        self.local_logger.error(json.dumps(entry))

    def warning(self, message: str, **kwargs):
        """Log warning level message."""
        entry = self._build_log_entry('WARNING', message, **kwargs)

        if self.cloud_logger:
            self.cloud_logger.log_struct(entry, severity='WARNING')

        self.local_logger.warning(json.dumps(entry))

    def debug(self, message: str, **kwargs):
        """Log debug level message."""
        entry = self._build_log_entry('DEBUG', message, **kwargs)

        if self.cloud_logger:
            self.cloud_logger.log_struct(entry, severity='DEBUG')

        self.local_logger.debug(json.dumps(entry))

    def _get_traceback(self, error: Exception) -> str:
        """Get formatted traceback."""
        return ''.join(traceback.format_exception(
            type(error),
            error,
            error.__traceback__
        ))


# Create logger instances for each service
api_logger = StructuredLogger('api-gateway')
invoice_logger = StructuredLogger('invoice-worker')
ocr_logger = StructuredLogger('ocr-worker')
summarizer_logger = StructuredLogger('summarizer-worker')
rag_ingest_logger = StructuredLogger('rag-ingest-worker')
rag_query_logger = StructuredLogger('rag-query-worker')
filling_logger = StructuredLogger('filling-worker')
