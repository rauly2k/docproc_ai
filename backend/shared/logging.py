"""Structured logging for Cloud Logging (Phase 7.2)."""

import logging
import json
from typing import Any, Dict
from datetime import datetime
from google.cloud import logging as cloud_logging
from contextvars import ContextVar
import traceback

from .config import get_settings

settings = get_settings()

# Context variables for request tracing
request_id_var: ContextVar[str] = ContextVar('request_id', default='')
tenant_id_var: ContextVar[str] = ContextVar('tenant_id', default='')


class StructuredLogger:
    """Google Cloud Logging compatible structured logger."""

    def __init__(self, service_name: str):
        self.service_name = service_name

        # Initialize Cloud Logging client (if in production)
        if settings.environment == "production":
            try:
                self.client = cloud_logging.Client()
                self.logger = self.client.logger(service_name)
            except Exception as e:
                print(f"Failed to initialize Cloud Logging: {e}")
                self.logger = None
        else:
            self.logger = None

        # Also setup Python logging for local development
        logging.basicConfig(
            level=logging.DEBUG if settings.debug else logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.local_logger = logging.getLogger(service_name)

    def _build_log_entry(self, level: str, message: str, **kwargs) -> Dict[str, Any]:
        """Build structured log entry."""
        entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'severity': level,
            'message': message,
            'service': self.service_name,
            'request_id': request_id_var.get(),
            'tenant_id': tenant_id_var.get(),
            'environment': settings.environment,
        }

        # Add any additional fields
        entry.update(kwargs)

        return entry

    def info(self, message: str, **kwargs):
        """Log info level message."""
        entry = self._build_log_entry('INFO', message, **kwargs)

        if self.logger:
            self.logger.log_struct(entry, severity='INFO')

        self.local_logger.info(json.dumps(entry))

    def error(self, message: str, error: Exception = None, **kwargs):
        """Log error level message."""
        entry = self._build_log_entry('ERROR', message, **kwargs)

        if error:
            entry['error'] = {
                'type': type(error).__name__,
                'message': str(error),
                'traceback': self._get_traceback(error)
            }

        if self.logger:
            self.logger.log_struct(entry, severity='ERROR')

        self.local_logger.error(json.dumps(entry))

    def warning(self, message: str, **kwargs):
        """Log warning level message."""
        entry = self._build_log_entry('WARNING', message, **kwargs)

        if self.logger:
            self.logger.log_struct(entry, severity='WARNING')

        self.local_logger.warning(json.dumps(entry))

    def debug(self, message: str, **kwargs):
        """Log debug level message."""
        if settings.debug:
            entry = self._build_log_entry('DEBUG', message, **kwargs)

            if self.logger:
                self.logger.log_struct(entry, severity='DEBUG')

            self.local_logger.debug(json.dumps(entry))

    def _get_traceback(self, error: Exception) -> str:
        """Get formatted traceback."""
        return ''.join(traceback.format_exception(type(error), error, error.__traceback__))


# Create logger instances for different services
api_logger = StructuredLogger('api-gateway')
invoice_logger = StructuredLogger('invoice-worker')
ocr_logger = StructuredLogger('ocr-worker')
summarizer_logger = StructuredLogger('summarizer-worker')
rag_logger = StructuredLogger('rag-worker')
filling_logger = StructuredLogger('filling-worker')
