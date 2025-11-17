# Phase 7: Polish and Beta Launch (Weeks 11-12)

**Timeline**: Weeks 11-12
**Estimated Effort**: ~80 hours
**Dependencies**: All previous phases (0-6) completed and tested

## Overview

Phase 7 focuses on production readiness, polish, and successful beta launch. This includes frontend refinement, comprehensive monitoring, performance optimization, security hardening, documentation, and beta user onboarding.

## Prerequisites

- All 5 AI features deployed and functional (Phases 1-6)
- All Cloud Run services running without errors
- Database fully migrated with all tables
- Basic end-to-end testing completed
- At least 10 beta users identified and committed

---

## Task 7.1: Frontend Polish and User Experience (16 hours)

### Objective
Transform MVP frontend into polished, professional application with excellent UX.

### Subtasks

#### 7.1.1: Implement Loading States and Skeletons (4 hours)

**Create skeleton components** (`frontend/src/components/common/Skeleton.tsx`):

```typescript
import React from 'react';

interface SkeletonProps {
  variant?: 'text' | 'circular' | 'rectangular';
  width?: string | number;
  height?: string | number;
  className?: string;
}

export const Skeleton: React.FC<SkeletonProps> = ({
  variant = 'text',
  width,
  height,
  className = ''
}) => {
  const baseClasses = 'animate-pulse bg-gray-200 dark:bg-gray-700';

  const variantClasses = {
    text: 'h-4 rounded',
    circular: 'rounded-full',
    rectangular: 'rounded-md'
  };

  const style = {
    width: width || (variant === 'text' ? '100%' : undefined),
    height: height || (variant === 'text' ? undefined : '100%')
  };

  return (
    <div
      className={`${baseClasses} ${variantClasses[variant]} ${className}`}
      style={style}
    />
  );
};

// Document list skeleton
export const DocumentListSkeleton: React.FC = () => {
  return (
    <div className="space-y-4">
      {[1, 2, 3, 4, 5].map((i) => (
        <div key={i} className="border border-gray-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <Skeleton width="60%" height={20} className="mb-2" />
              <Skeleton width="40%" height={16} />
            </div>
            <Skeleton variant="rectangular" width={100} height={36} />
          </div>
        </div>
      ))}
    </div>
  );
};
```

**Update document list with loading states** (`frontend/src/components/documents/DocumentList.tsx`):

```typescript
import { DocumentListSkeleton } from '../common/Skeleton';

const DocumentList: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get('/documents');
      setDocuments(response.data.documents);
    } catch (err) {
      setError('Failed to load documents. Please try again.');
      console.error('Error fetching documents:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <DocumentListSkeleton />;

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600 mb-4">{error}</p>
        <button
          onClick={fetchDocuments}
          className="btn btn-primary"
        >
          Retry
        </button>
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500 mb-4">No documents uploaded yet</p>
        <Link to="/upload" className="btn btn-primary">
          Upload Your First Document
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {documents.map(doc => (
        <DocumentCard key={doc.id} document={doc} />
      ))}
    </div>
  );
};
```

#### 7.1.2: Comprehensive Error Handling (4 hours)

**Create error boundary** (`frontend/src/components/common/ErrorBoundary.tsx`):

```typescript
import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo);

    // Send to error tracking service (Sentry, etc.)
    if (window.Sentry) {
      window.Sentry.captureException(error, {
        contexts: { react: { componentStack: errorInfo.componentStack } }
      });
    }
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <div className="max-w-md w-full bg-white shadow-lg rounded-lg p-6">
            <div className="text-center">
              <h1 className="text-2xl font-bold text-gray-900 mb-4">
                Something went wrong
              </h1>
              <p className="text-gray-600 mb-6">
                We're sorry for the inconvenience. Please try refreshing the page.
              </p>
              <button
                onClick={() => window.location.reload()}
                className="btn btn-primary w-full"
              >
                Refresh Page
              </button>
              {process.env.NODE_ENV === 'development' && (
                <details className="mt-4 text-left">
                  <summary className="cursor-pointer text-sm text-gray-500">
                    Error details
                  </summary>
                  <pre className="mt-2 text-xs bg-gray-100 p-2 rounded overflow-auto">
                    {this.state.error?.toString()}
                  </pre>
                </details>
              )}
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
```

**Create API error handler** (`frontend/src/services/api.ts`):

```typescript
import axios, { AxiosError } from 'axios';

// Add error interceptor
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    if (error.response) {
      const status = error.response.status;
      const data = error.response.data as any;

      // Handle specific error codes
      switch (status) {
        case 401:
          // Token expired, try to refresh
          try {
            const user = auth.currentUser;
            if (user) {
              const newToken = await user.getIdToken(true);
              api.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;
              // Retry original request
              return api.request(error.config!);
            }
          } catch (refreshError) {
            // Redirect to login
            window.location.href = '/login';
          }
          break;

        case 403:
          toast.error('You do not have permission to perform this action');
          break;

        case 404:
          toast.error('Resource not found');
          break;

        case 413:
          toast.error('File size too large. Maximum size is 50MB');
          break;

        case 429:
          toast.error('Too many requests. Please try again later');
          break;

        case 500:
          toast.error('Server error. Our team has been notified');
          break;

        default:
          toast.error(data.detail || 'An unexpected error occurred');
      }
    } else if (error.request) {
      toast.error('Network error. Please check your connection');
    }

    return Promise.reject(error);
  }
);
```

#### 7.1.3: Responsive Design Audit (4 hours)

**Mobile-first breakpoint system** (`frontend/tailwind.config.js`):

```javascript
module.exports = {
  theme: {
    screens: {
      'sm': '640px',   // Mobile landscape
      'md': '768px',   // Tablet
      'lg': '1024px',  // Desktop
      'xl': '1280px',  // Large desktop
      '2xl': '1536px', // Extra large
    },
  },
};
```

**Responsive document viewer** (`frontend/src/components/documents/DocumentViewer.tsx`):

```typescript
const DocumentViewer: React.FC<{ document: Document }> = ({ document }) => {
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 768);
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  if (isMobile) {
    // Stacked layout for mobile
    return (
      <div className="space-y-4">
        <div className="bg-white rounded-lg shadow p-4">
          <h2 className="text-lg font-semibold mb-4">Document Preview</h2>
          <PDFPreview url={document.gcs_uri} />
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <h2 className="text-lg font-semibold mb-4">Extracted Data</h2>
          <InvoiceDataDisplay data={document.invoice_data} />
        </div>
      </div>
    );
  }

  // Side-by-side layout for desktop
  return (
    <div className="grid grid-cols-2 gap-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Document Preview</h2>
        <PDFPreview url={document.gcs_uri} />
      </div>
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Extracted Data</h2>
        <InvoiceDataDisplay data={document.invoice_data} />
      </div>
    </div>
  );
};
```

#### 7.1.4: Accessibility Improvements (4 hours)

**Add ARIA labels and keyboard navigation**:

```typescript
// Upload button with accessibility
<button
  onClick={handleUpload}
  className="btn btn-primary"
  aria-label="Upload document"
  disabled={uploading}
>
  {uploading ? (
    <>
      <span className="sr-only">Uploading...</span>
      <Spinner aria-hidden="true" />
    </>
  ) : (
    'Upload Document'
  )}
</button>

// Modal with focus trap
const Modal: React.FC<ModalProps> = ({ isOpen, onClose, children }) => {
  const modalRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen) {
      modalRef.current?.focus();
      // Trap focus inside modal
      const handleKeyDown = (e: KeyboardEvent) => {
        if (e.key === 'Escape') onClose();
      };
      document.addEventListener('keydown', handleKeyDown);
      return () => document.removeEventListener('keydown', handleKeyDown);
    }
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      role="dialog"
      aria-modal="true"
      ref={modalRef}
      tabIndex={-1}
    >
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
        {children}
      </div>
    </div>
  );
};
```

**Contrast ratio verification**:

```bash
# Install accessibility testing tools
npm install --save-dev @axe-core/react

# frontend/src/index.tsx
if (process.env.NODE_ENV === 'development') {
  import('@axe-core/react').then(axe => {
    axe.default(React, ReactDOM, 1000);
  });
}
```

### Verification

```bash
# Run on all devices
npm run build
npm run preview

# Test on:
# - Mobile (375px width - iPhone SE)
# - Tablet (768px width - iPad)
# - Desktop (1440px width)
# - Check all features work on each breakpoint
# - Verify loading states appear correctly
# - Test error scenarios (network offline, API down)
# - Run Lighthouse audit (target: 90+ accessibility score)

npx lighthouse http://localhost:3000 --view
```

---

## Task 7.2: Monitoring and Logging Infrastructure (16 hours)

### Objective
Implement comprehensive monitoring, logging, and alerting for production operations.

### Subtasks

#### 7.2.1: Cloud Logging Setup (4 hours)

**Structured logging utility** (`backend/shared/logging.py`):

```python
import logging
import json
from typing import Any, Dict
from datetime import datetime
from google.cloud import logging as cloud_logging
from contextvars import ContextVar

# Context variables for request tracing
request_id_var: ContextVar[str] = ContextVar('request_id', default='')
tenant_id_var: ContextVar[str] = ContextVar('tenant_id', default='')

class StructuredLogger:
    """Google Cloud Logging compatible structured logger"""

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.client = cloud_logging.Client()
        self.logger = self.client.logger(service_name)

        # Also setup Python logging for local development
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.local_logger = logging.getLogger(service_name)

    def _build_log_entry(self, level: str, message: str, **kwargs) -> Dict[str, Any]:
        """Build structured log entry"""
        entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'severity': level,
            'message': message,
            'service': self.service_name,
            'request_id': request_id_var.get(),
            'tenant_id': tenant_id_var.get(),
        }

        # Add any additional fields
        entry.update(kwargs)

        return entry

    def info(self, message: str, **kwargs):
        """Log info level message"""
        entry = self._build_log_entry('INFO', message, **kwargs)
        self.logger.log_struct(entry, severity='INFO')
        self.local_logger.info(json.dumps(entry))

    def error(self, message: str, error: Exception = None, **kwargs):
        """Log error level message"""
        entry = self._build_log_entry('ERROR', message, **kwargs)
        if error:
            entry['error'] = {
                'type': type(error).__name__,
                'message': str(error),
                'traceback': self._get_traceback(error)
            }
        self.logger.log_struct(entry, severity='ERROR')
        self.local_logger.error(json.dumps(entry))

    def warning(self, message: str, **kwargs):
        """Log warning level message"""
        entry = self._build_log_entry('WARNING', message, **kwargs)
        self.logger.log_struct(entry, severity='WARNING')
        self.local_logger.warning(json.dumps(entry))

    def _get_traceback(self, error: Exception) -> str:
        """Get formatted traceback"""
        import traceback
        return ''.join(traceback.format_exception(type(error), error, error.__traceback__))

# Create logger instances
api_logger = StructuredLogger('api-gateway')
invoice_logger = StructuredLogger('invoice-worker')
ocr_logger = StructuredLogger('ocr-worker')
summarizer_logger = StructuredLogger('summarizer-worker')
rag_logger = StructuredLogger('rag-worker')
filling_logger = StructuredLogger('filling-worker')
```

**Add logging middleware** (`backend/api_gateway/middleware.py`):

```python
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from backend.shared.logging import api_logger, request_id_var, tenant_id_var
from time import time

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all requests with structured logging"""

    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = str(uuid.uuid4())
        request_id_var.set(request_id)

        # Extract tenant_id from auth if available
        if hasattr(request.state, 'tenant_id'):
            tenant_id_var.set(request.state.tenant_id)

        # Log request
        start_time = time()
        api_logger.info(
            f"{request.method} {request.url.path}",
            method=request.method,
            path=request.url.path,
            query_params=dict(request.query_params),
            client_ip=request.client.host if request.client else None
        )

        # Process request
        try:
            response = await call_next(request)
            duration = time() - start_time

            # Log response
            api_logger.info(
                f"Response {response.status_code}",
                status_code=response.status_code,
                duration_ms=round(duration * 1000, 2)
            )

            # Add request ID to response headers
            response.headers['X-Request-ID'] = request_id
            return response

        except Exception as e:
            duration = time() - start_time
            api_logger.error(
                "Request failed",
                error=e,
                duration_ms=round(duration * 1000, 2)
            )
            raise

# Add to FastAPI app
app.add_middleware(LoggingMiddleware)
```

#### 7.2.2: Cloud Monitoring Dashboards (4 hours)

**Create monitoring dashboard with Terraform** (`terraform/modules/monitoring/main.tf`):

```hcl
# Cloud Monitoring Dashboard
resource "google_monitoring_dashboard" "main" {
  dashboard_json = jsonencode({
    displayName = "Document AI SaaS - Main Dashboard"

    gridLayout = {
      widgets = [
        # API Gateway Request Rate
        {
          title = "API Gateway - Requests per minute"
          xyChart = {
            dataSets = [{
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"api-gateway\" AND metric.type=\"run.googleapis.com/request_count\""
                  aggregation = {
                    alignmentPeriod = "60s"
                    perSeriesAligner = "ALIGN_RATE"
                  }
                }
              }
            }]
          }
        },

        # API Gateway Response Times
        {
          title = "API Gateway - Response Latency (p50, p95, p99)"
          xyChart = {
            dataSets = [{
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"api-gateway\" AND metric.type=\"run.googleapis.com/request_latencies\""
                  aggregation = {
                    alignmentPeriod = "60s"
                    perSeriesAligner = "ALIGN_DELTA"
                    crossSeriesReducer = "REDUCE_PERCENTILE_50"
                  }
                }
              }
            }]
          }
        },

        # Error Rate
        {
          title = "API Gateway - Error Rate (%)"
          xyChart = {
            dataSets = [{
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "resource.type=\"cloud_run_revision\" AND metric.type=\"logging.googleapis.com/log_entry_count\" AND jsonPayload.severity=\"ERROR\""
                  aggregation = {
                    alignmentPeriod = "60s"
                    perSeriesAligner = "ALIGN_RATE"
                  }
                }
              }
            }]
          }
        },

        # Document Processing Queue Depth
        {
          title = "Pub/Sub - Queue Depth by Topic"
          xyChart = {
            dataSets = [{
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "resource.type=\"pubsub_topic\" AND metric.type=\"pubsub.googleapis.com/topic/num_unacked_messages_by_region\""
                  aggregation = {
                    alignmentPeriod = "60s"
                    perSeriesAligner = "ALIGN_MEAN"
                    groupByFields = ["resource.topic_id"]
                  }
                }
              }
            }]
          }
        },

        # Database Connections
        {
          title = "Cloud SQL - Active Connections"
          xyChart = {
            dataSets = [{
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "resource.type=\"cloudsql_database\" AND metric.type=\"cloudsql.googleapis.com/database/postgresql/num_backends\""
                  aggregation = {
                    alignmentPeriod = "60s"
                    perSeriesAligner = "ALIGN_MEAN"
                  }
                }
              }
            }]
          }
        },

        # Worker Processing Times
        {
          title = "Workers - Average Processing Time by Worker"
          xyChart = {
            dataSets = [{
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "resource.type=\"cloud_run_revision\" AND metric.type=\"logging.googleapis.com/user/processing_duration\""
                  aggregation = {
                    alignmentPeriod = "60s"
                    perSeriesAligner = "ALIGN_MEAN"
                    groupByFields = ["resource.service_name"]
                  }
                }
              }
            }]
          }
        }
      ]
    }
  })
}

# Uptime Check for API Gateway
resource "google_monitoring_uptime_check_config" "api_gateway" {
  display_name = "API Gateway Health Check"
  timeout      = "10s"
  period       = "60s"

  http_check {
    path         = "/health"
    port         = "443"
    use_ssl      = true
    validate_ssl = true
  }

  monitored_resource {
    type = "uptime_url"
    labels = {
      project_id = var.project_id
      host       = google_cloud_run_service.api_gateway.status[0].url
    }
  }
}
```

**Create alert policies** (`terraform/modules/monitoring/alerts.tf`):

```hcl
# High Error Rate Alert
resource "google_monitoring_alert_policy" "high_error_rate" {
  display_name = "High Error Rate"
  combiner     = "OR"

  conditions {
    display_name = "Error rate > 5%"

    condition_threshold {
      filter          = "resource.type=\"cloud_run_revision\" AND metric.type=\"logging.googleapis.com/log_entry_count\" AND jsonPayload.severity=\"ERROR\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0.05

      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }

  notification_channels = [google_monitoring_notification_channel.email.id]

  alert_strategy {
    auto_close = "1800s"
  }
}

# API Downtime Alert
resource "google_monitoring_alert_policy" "api_down" {
  display_name = "API Gateway Down"
  combiner     = "OR"

  conditions {
    display_name = "Uptime check failed"

    condition_threshold {
      filter          = "metric.type=\"monitoring.googleapis.com/uptime_check/check_passed\" AND resource.type=\"uptime_url\""
      duration        = "60s"
      comparison      = "COMPARISON_GT"
      threshold_value = 1

      aggregations {
        alignment_period     = "1200s"
        cross_series_reducer = "REDUCE_COUNT_FALSE"
        per_series_aligner   = "ALIGN_NEXT_OLDER"
      }
    }
  }

  notification_channels = [google_monitoring_notification_channel.email.id]

  alert_strategy {
    auto_close = "1800s"
  }
}

# Notification Channel
resource "google_monitoring_notification_channel" "email" {
  display_name = "Email Notification"
  type         = "email"

  labels = {
    email_address = var.alert_email
  }
}
```

#### 7.2.3: Sentry Integration for Frontend (4 hours)

**Install Sentry**:

```bash
npm install @sentry/react @sentry/tracing
```

**Configure Sentry** (`frontend/src/services/sentry.ts`):

```typescript
import * as Sentry from '@sentry/react';
import { BrowserTracing } from '@sentry/tracing';

export const initSentry = () => {
  if (import.meta.env.PROD) {
    Sentry.init({
      dsn: import.meta.env.VITE_SENTRY_DSN,
      integrations: [new BrowserTracing()],

      // Performance monitoring
      tracesSampleRate: 0.1, // 10% of transactions

      // Release tracking
      release: import.meta.env.VITE_APP_VERSION,
      environment: import.meta.env.VITE_ENVIRONMENT || 'production',

      // User context
      beforeSend(event, hint) {
        // Add user context if authenticated
        const user = auth.currentUser;
        if (user) {
          event.user = {
            id: user.uid,
            email: user.email || undefined
          };
        }
        return event;
      },

      // Filter out known issues
      ignoreErrors: [
        'ResizeObserver loop limit exceeded',
        'Non-Error promise rejection captured'
      ]
    });
  }
};

// Capture custom events
export const captureMessage = (message: string, level: Sentry.SeverityLevel = 'info') => {
  Sentry.captureMessage(message, level);
};

export const captureException = (error: Error, context?: Record<string, any>) => {
  Sentry.captureException(error, { contexts: { custom: context } });
};
```

**Add to main app** (`frontend/src/main.tsx`):

```typescript
import { initSentry } from './services/sentry';

// Initialize Sentry before React
initSentry();

// Wrap app with Sentry ErrorBoundary
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <Sentry.ErrorBoundary fallback={<ErrorFallback />}>
      <App />
    </Sentry.ErrorBoundary>
  </React.StrictMode>
);
```

#### 7.2.4: Custom Metrics and Performance Tracking (4 hours)

**Add custom metrics to workers** (`backend/workers/invoice_worker/processor.py`):

```python
from google.cloud import monitoring_v3
from time import time
from backend.shared.logging import invoice_logger

class InvoiceProcessor:
    def __init__(self):
        # ... existing init
        self.metrics_client = monitoring_v3.MetricServiceClient()
        self.project_name = f"projects/{settings.project_id}"

    def _record_processing_time(self, duration_seconds: float, success: bool):
        """Record custom metric for processing duration"""
        series = monitoring_v3.TimeSeries()
        series.metric.type = 'custom.googleapis.com/invoice_worker/processing_duration'
        series.resource.type = 'cloud_run_revision'
        series.resource.labels['service_name'] = 'invoice-worker'
        series.resource.labels['project_id'] = settings.project_id

        # Add metric labels
        series.metric.labels['success'] = str(success).lower()

        # Add data point
        now = time.time()
        interval = monitoring_v3.TimeInterval({"end_time": {"seconds": int(now)}})
        point = monitoring_v3.Point({
            "interval": interval,
            "value": {"double_value": duration_seconds}
        })
        series.points = [point]

        # Write metric
        self.metrics_client.create_time_series(
            name=self.project_name,
            time_series=[series]
        )

    def process_invoice(self, document_id: str, gcs_uri: str, db_session):
        """Process invoice with timing metrics"""
        start_time = time()
        success = False

        try:
            invoice_logger.info(
                "Starting invoice processing",
                document_id=document_id,
                gcs_uri=gcs_uri
            )

            # ... existing processing logic

            success = True
            invoice_logger.info(
                "Invoice processing completed",
                document_id=document_id,
                duration_seconds=time() - start_time
            )

        except Exception as e:
            invoice_logger.error(
                "Invoice processing failed",
                document_id=document_id,
                error=e,
                duration_seconds=time() - start_time
            )
            raise

        finally:
            # Record metric
            self._record_processing_time(time() - start_time, success)
```

### Verification

```bash
# Deploy monitoring infrastructure
cd terraform/modules/monitoring
terraform init
terraform apply

# View dashboard
echo "Dashboard URL:"
echo "https://console.cloud.google.com/monitoring/dashboards"

# Test alerts by simulating errors
# Trigger 500 errors on API endpoint and verify alert fires

# Verify Sentry integration
# Trigger error in frontend and check Sentry dashboard

# Check custom metrics
gcloud monitoring time-series list \
  --filter='metric.type="custom.googleapis.com/invoice_worker/processing_duration"' \
  --format=json
```

---

## Task 7.3: Performance Optimization (20 hours)

### Objective
Optimize application performance for production scale.

### Subtasks

#### 7.3.1: Database Optimization (8 hours)

**Create indexes for common queries** (`backend/alembic/versions/006_performance_indexes.py`):

```python
"""Add performance indexes

Revision ID: 006
Revises: 005
Create Date: 2025-11-17
"""
from alembic import op

def upgrade():
    # Documents table indexes
    op.create_index(
        'idx_documents_tenant_created',
        'documents',
        ['tenant_id', 'created_at'],
        postgresql_using='btree'
    )

    op.create_index(
        'idx_documents_tenant_status',
        'documents',
        ['tenant_id', 'status'],
        postgresql_using='btree'
    )

    op.create_index(
        'idx_documents_tenant_type',
        'documents',
        ['tenant_id', 'document_type'],
        postgresql_using='btree'
    )

    # Processing jobs indexes
    op.create_index(
        'idx_jobs_tenant_created',
        'processing_jobs',
        ['tenant_id', 'created_at'],
        postgresql_using='btree'
    )

    op.create_index(
        'idx_jobs_document_status',
        'processing_jobs',
        ['document_id', 'status'],
        postgresql_using='btree'
    )

    # Document chunks indexes for RAG
    op.create_index(
        'idx_chunks_tenant_document',
        'document_chunks',
        ['tenant_id', 'document_id'],
        postgresql_using='btree'
    )

    # IMPORTANT: pgvector HNSW index for fast similarity search
    op.execute("""
        CREATE INDEX idx_chunks_embedding_hnsw
        ON document_chunks
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
    """)

    # Chat messages indexes
    op.create_index(
        'idx_messages_session_created',
        'chat_messages',
        ['session_id', 'created_at'],
        postgresql_using='btree'
    )

    # Audit logs indexes (for compliance queries)
    op.create_index(
        'idx_audit_tenant_timestamp',
        'audit_logs',
        ['tenant_id', 'timestamp'],
        postgresql_using='btree'
    )

    op.create_index(
        'idx_audit_user_action',
        'audit_logs',
        ['user_id', 'action'],
        postgresql_using='btree'
    )

def downgrade():
    op.drop_index('idx_documents_tenant_created')
    op.drop_index('idx_documents_tenant_status')
    op.drop_index('idx_documents_tenant_type')
    op.drop_index('idx_jobs_tenant_created')
    op.drop_index('idx_jobs_document_status')
    op.drop_index('idx_chunks_tenant_document')
    op.drop_index('idx_chunks_embedding_hnsw')
    op.drop_index('idx_messages_session_created')
    op.drop_index('idx_audit_tenant_timestamp')
    op.drop_index('idx_audit_user_action')
```

**Apply migration**:

```bash
cd backend
alembic upgrade head

# Analyze tables after indexing
python scripts/analyze_database.py
```

**Database connection pooling optimization** (`backend/shared/database.py`):

```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

# Optimized connection pool for Cloud Run
engine = create_engine(
    settings.database_url,
    poolclass=QueuePool,
    pool_size=5,              # Small pool for serverless
    max_overflow=10,          # Allow burst
    pool_timeout=30,          # Connection timeout
    pool_recycle=1800,        # Recycle connections every 30 min
    pool_pre_ping=True,       # Test connections before use
    echo=False,               # Disable SQL logging in production
    connect_args={
        "connect_timeout": 10,
        "options": "-c statement_timeout=30000"  # 30s query timeout
    }
)
```

**Query optimization for document list** (`backend/api_gateway/routes/documents.py`):

```python
from sqlalchemy.orm import selectinload

@router.get("/documents")
async def list_documents(
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None,
    document_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List documents with optimized query"""
    tenant_id = current_user["tenant_id"]

    # Build query with eager loading to avoid N+1
    query = db.query(Document).filter(Document.tenant_id == tenant_id)

    # Add filters
    if status:
        query = query.filter(Document.status == status)
    if document_type:
        query = query.filter(Document.document_type == document_type)

    # Eager load related data
    query = query.options(
        selectinload(Document.processing_jobs),
        selectinload(Document.invoice_data),
        selectinload(Document.ocr_results)
    )

    # Order by most recent first (uses index)
    query = query.order_by(Document.created_at.desc())

    # Paginate
    total = query.count()
    documents = query.offset(skip).limit(limit).all()

    return {
        "documents": documents,
        "total": total,
        "skip": skip,
        "limit": limit
    }
```

#### 7.3.2: API Response Caching (4 hours)

**Install Redis for caching**:

```bash
# Add to terraform/modules/redis/main.tf
resource "google_redis_instance" "cache" {
  name               = "document-ai-cache"
  tier               = "BASIC"
  memory_size_gb     = 1
  region             = var.region
  redis_version      = "REDIS_7_0"
  display_name       = "Document AI Cache"

  auth_enabled       = true
  transit_encryption_mode = "SERVER_AUTHENTICATION"
}

output "redis_host" {
  value = google_redis_instance.cache.host
}

output "redis_port" {
  value = google_redis_instance.cache.port
}
```

**Implement caching layer** (`backend/shared/cache.py`):

```python
import redis
import json
from typing import Optional, Any
from functools import wraps

class CacheManager:
    def __init__(self):
        self.client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            password=settings.redis_auth,
            ssl=True,
            decode_responses=True
        )

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            value = self.client.get(key)
            return json.loads(value) if value else None
        except Exception as e:
            # Fail gracefully - cache miss on error
            return None

    def set(self, key: str, value: Any, ttl: int = 300):
        """Set value in cache with TTL (default 5 minutes)"""
        try:
            self.client.setex(key, ttl, json.dumps(value))
        except Exception as e:
            # Fail gracefully - don't break app on cache errors
            pass

    def delete(self, key: str):
        """Delete key from cache"""
        try:
            self.client.delete(key)
        except Exception:
            pass

    def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching pattern"""
        try:
            keys = self.client.keys(pattern)
            if keys:
                self.client.delete(*keys)
        except Exception:
            pass

cache = CacheManager()

def cached(key_prefix: str, ttl: int = 300):
    """Decorator for caching function results"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key
            cache_key = f"{key_prefix}:{':'.join(str(arg) for arg in args)}"

            # Try cache first
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result
            cache.set(cache_key, result, ttl)

            return result
        return wrapper
    return decorator
```

**Apply caching to API endpoints** (`backend/api_gateway/routes/documents.py`):

```python
from backend.shared.cache import cache, cached

@router.get("/documents/{document_id}")
@cached(key_prefix="document", ttl=300)  # Cache for 5 minutes
async def get_document(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get document with caching"""
    tenant_id = current_user["tenant_id"]

    document = db.query(Document).filter(
        Document.id == document_id,
        Document.tenant_id == tenant_id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return document

@router.patch("/documents/{document_id}")
async def update_document(
    document_id: str,
    updates: DocumentUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update document and invalidate cache"""
    # ... update logic

    # Invalidate cache for this document
    cache.delete(f"document:{document_id}")

    return updated_document
```

#### 7.3.3: Cloud Run Optimization (4 hours)

**Optimize Cloud Run configurations** (`terraform/modules/cloud_run/main.tf`):

```hcl
# API Gateway with optimized settings
resource "google_cloud_run_service" "api_gateway" {
  name     = "api-gateway"
  location = var.region

  template {
    metadata {
      annotations = {
        # CPU allocation
        "autoscaling.knative.dev/minScale"      = "1"    # Always warm
        "autoscaling.knative.dev/maxScale"      = "10"
        "run.googleapis.com/cpu-throttling"     = "false" # No throttling

        # Startup optimization
        "run.googleapis.com/startup-cpu-boost"  = "true"

        # Connection settings
        "run.googleapis.com/cloudsql-instances" = google_sql_database_instance.main.connection_name
      }
    }

    spec {
      container_concurrency = 80  # Handle 80 concurrent requests per instance
      timeout_seconds       = 300 # 5 minute timeout

      containers {
        image = "gcr.io/${var.project_id}/api-gateway:latest"

        resources {
          limits = {
            cpu    = "2"      # 2 vCPU
            memory = "1Gi"    # 1 GB RAM
          }
        }

        # Liveness probe
        liveness_probe {
          http_get {
            path = "/health"
          }
          initial_delay_seconds = 10
          period_seconds        = 10
        }

        env {
          name  = "WORKERS"
          value = "4"  # Uvicorn workers
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}

# Worker services - optimized for background processing
resource "google_cloud_run_service" "invoice_worker" {
  name     = "invoice-worker"
  location = var.region

  template {
    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale" = "0"   # Scale to zero when idle
        "autoscaling.knative.dev/maxScale" = "5"
        "run.googleapis.com/cpu-throttling" = "false"
      }
    }

    spec {
      container_concurrency = 1  # Process one job at a time
      timeout_seconds       = 900 # 15 minute timeout for long processing

      containers {
        image = "gcr.io/${var.project_id}/invoice-worker:latest"

        resources {
          limits = {
            cpu    = "2"
            memory = "2Gi"  # More memory for Document AI processing
          }
        }
      }
    }
  }
}
```

**Optimize FastAPI startup** (`backend/api_gateway/main.py`):

```python
from fastapi import FastAPI
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for warmup"""
    # Startup: Warm up connections
    print("Warming up application...")

    # Pre-initialize database connection
    with next(get_db()) as db:
        db.execute("SELECT 1")

    # Pre-initialize GCS client
    storage_client = storage.Client()

    # Pre-initialize Redis
    cache.client.ping()

    print("Application ready")

    yield

    # Shutdown
    print("Shutting down...")

app = FastAPI(
    title="Document AI SaaS API",
    lifespan=lifespan
)

# Use Uvicorn with multiple workers for better concurrency
# In Dockerfile CMD:
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "4"]
```

#### 7.3.4: Frontend Build Optimization (4 hours)

**Optimize Vite build** (`frontend/vite.config.ts`):

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { visualizer } from 'rollup-plugin-visualizer';

export default defineConfig({
  plugins: [
    react(),
    visualizer({ filename: './dist/stats.html' }) // Bundle analyzer
  ],

  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          // Split vendor code
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'firebase': ['firebase/app', 'firebase/auth'],
          'ui-vendor': ['@headlessui/react', '@heroicons/react']
        }
      }
    },

    // Compress assets
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true  // Remove console.logs in production
      }
    },

    // Source maps for error tracking
    sourcemap: true
  },

  // Optimize dependency pre-bundling
  optimizeDeps: {
    include: ['react', 'react-dom', 'firebase/app', 'firebase/auth']
  }
});
```

**Implement code splitting** (`frontend/src/App.tsx`):

```typescript
import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';

// Lazy load pages
const Dashboard = lazy(() => import('./pages/Dashboard'));
const DocumentUpload = lazy(() => import('./pages/DocumentUpload'));
const InvoiceViewer = lazy(() => import('./pages/InvoiceViewer'));
const OCRResults = lazy(() => import('./pages/OCRResults'));
const Summarization = lazy(() => import('./pages/Summarization'));
const ChatWithPDF = lazy(() => import('./pages/ChatWithPDF'));
const DocumentFilling = lazy(() => import('./pages/DocumentFilling'));

const LoadingFallback = () => (
  <div className="flex items-center justify-center min-h-screen">
    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
  </div>
);

function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<LoadingFallback />}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/upload" element={<DocumentUpload />} />
          <Route path="/invoice/:id" element={<InvoiceViewer />} />
          <Route path="/ocr/:id" element={<OCRResults />} />
          <Route path="/summarize/:id" element={<Summarization />} />
          <Route path="/chat/:id" element={<ChatWithPDF />} />
          <Route path="/fill" element={<DocumentFilling />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}
```

### Verification

```bash
# Database
# Check index usage
psql -h $DB_HOST -U postgres -d documentai -c "\d+ documents"
psql -h $DB_HOST -U postgres -d documentai -c "EXPLAIN ANALYZE SELECT * FROM documents WHERE tenant_id = 'test' ORDER BY created_at DESC LIMIT 20;"

# Cloud Run
# Deploy optimized configurations
cd terraform
terraform apply

# Load test API
npm install -g artillery
artillery quick --count 50 --num 100 https://api-gateway-xxx.run.app/health

# Frontend
# Build and analyze bundle
cd frontend
npm run build
# Open dist/stats.html to see bundle composition
# Target: < 500 KB initial bundle

# Check Lighthouse scores
npx lighthouse https://your-app.vercel.app --view
# Target: 90+ performance, 95+ accessibility
```

---

## Task 7.4: Security Hardening (12 hours)

### Objective
Implement security best practices and pass basic security audit.

### Subtasks

#### 7.4.1: Security Headers and CORS (3 hours)

**Add security headers** (`backend/api_gateway/middleware.py`):

```python
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.cors import CORSMiddleware

# Security headers middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # CSP header
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://apis.google.com; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https://firebaseapp.com https://identitytoolkit.googleapis.com; "
            "frame-ancestors 'none';"
        )

        return response

# Add to app
app.add_middleware(SecurityHeadersMiddleware)

# CORS with strict origin checking
allowed_origins = [
    settings.frontend_url,
    "https://your-app.vercel.app"
]

if settings.environment == "development":
    allowed_origins.append("http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
    max_age=3600
)

# Trusted host protection
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[
        "api-gateway-xxx.run.app",
        "localhost",
        "127.0.0.1"
    ]
)
```

#### 7.4.2: Input Validation and Sanitization (3 hours)

**Strengthen Pydantic schemas** (`backend/shared/schemas.py`):

```python
from pydantic import BaseModel, Field, validator, constr
from typing import Optional
import re

class DocumentUpload(BaseModel):
    """Validated document upload request"""

    filename: constr(min_length=1, max_length=255) = Field(
        ...,
        description="Original filename"
    )

    document_type: str = Field(
        ...,
        description="Type of document"
    )

    @validator('filename')
    def validate_filename(cls, v):
        """Sanitize filename - prevent path traversal"""
        # Remove any path components
        v = v.split('/')[-1].split('\\')[-1]

        # Only allow safe characters
        if not re.match(r'^[a-zA-Z0-9._-]+$', v):
            raise ValueError('Filename contains invalid characters')

        # Check extension
        allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
        if not any(v.lower().endswith(ext) for ext in allowed_extensions):
            raise ValueError(f'File type not allowed. Allowed: {allowed_extensions}')

        return v

    @validator('document_type')
    def validate_document_type(cls, v):
        """Validate document type is from allowed list"""
        allowed_types = ['invoice', 'receipt', 'contract', 'id_card', 'passport', 'generic']
        if v not in allowed_types:
            raise ValueError(f'Invalid document type. Allowed: {allowed_types}')
        return v

class InvoiceUpdate(BaseModel):
    """Validated invoice update request"""

    supplier_name: Optional[constr(max_length=200)] = None
    invoice_number: Optional[constr(max_length=100)] = None
    total_amount: Optional[float] = Field(None, ge=0, le=999999999)

    @validator('total_amount')
    def validate_amount(cls, v):
        """Ensure reasonable amount"""
        if v is not None and (v < 0 or v > 999999999):
            raise ValueError('Amount out of reasonable range')
        return v

class ChatMessage(BaseModel):
    """Validated chat message"""

    message: constr(min_length=1, max_length=5000) = Field(
        ...,
        description="User message"
    )

    @validator('message')
    def validate_message(cls, v):
        """Sanitize message - prevent injection"""
        # Remove null bytes
        v = v.replace('\x00', '')

        # Check for suspicious patterns (basic SQL injection detection)
        suspicious_patterns = [
            r'(union\s+select)',
            r'(insert\s+into)',
            r'(delete\s+from)',
            r'(drop\s+table)',
            r'(<script)',
        ]

        for pattern in suspicious_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError('Message contains prohibited content')

        return v.strip()
```

**SQL injection prevention** (already handled by SQLAlchemy ORM, but add extra layer):

```python
from sqlalchemy import text

# BAD - Never do this:
# db.execute(f"SELECT * FROM documents WHERE id = '{document_id}'")

# GOOD - Use parameterized queries:
db.execute(
    text("SELECT * FROM documents WHERE id = :doc_id"),
    {"doc_id": document_id}
)

# BEST - Use ORM:
db.query(Document).filter(Document.id == document_id).first()
```

#### 7.4.3: Rate Limiting (3 hours)

**Implement rate limiting** (`backend/shared/rate_limit.py`):

```python
from fastapi import HTTPException, Request
from typing import Callable
import time

class RateLimiter:
    """Token bucket rate limiter using Redis"""

    def __init__(self, redis_client):
        self.redis = redis_client

    def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> bool:
        """
        Check if request is within rate limit
        Returns True if allowed, False if rate limited
        """
        current = int(time.time())
        window_key = f"rate_limit:{key}:{current // window_seconds}"

        # Increment counter
        count = self.redis.incr(window_key)

        # Set expiry on first request in window
        if count == 1:
            self.redis.expire(window_key, window_seconds)

        return count <= max_requests

from backend.shared.cache import cache

rate_limiter = RateLimiter(cache.client)

def rate_limit(max_requests: int = 100, window_seconds: int = 60):
    """Decorator for rate limiting endpoints"""
    def decorator(func: Callable):
        async def wrapper(request: Request, *args, **kwargs):
            # Use IP address as rate limit key
            client_ip = request.client.host if request.client else "unknown"

            # For authenticated requests, use user ID
            if hasattr(request.state, 'user_id'):
                rate_key = f"user:{request.state.user_id}"
            else:
                rate_key = f"ip:{client_ip}"

            # Check rate limit
            if not rate_limiter.check_rate_limit(rate_key, max_requests, window_seconds):
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded. Please try again later.",
                    headers={"Retry-After": str(window_seconds)}
                )

            return await func(request, *args, **kwargs)

        return wrapper
    return decorator
```

**Apply to endpoints** (`backend/api_gateway/routes/documents.py`):

```python
from backend.shared.rate_limit import rate_limit

@router.post("/documents/upload")
@rate_limit(max_requests=10, window_seconds=60)  # 10 uploads per minute
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    # ... upload logic
    pass

@router.post("/chat/{session_id}/message")
@rate_limit(max_requests=30, window_seconds=60)  # 30 messages per minute
async def send_chat_message(
    request: Request,
    session_id: str,
    message: ChatMessage,
    current_user: dict = Depends(get_current_user),
):
    # ... chat logic
    pass
```

#### 7.4.4: Security Audit and Penetration Testing (3 hours)

**Install security scanning tools**:

```bash
# Backend security scan
pip install bandit safety

# Run Bandit (Python security linter)
bandit -r backend/ -f json -o security-report.json

# Check for known vulnerabilities
safety check --json

# Frontend security scan
npm audit
npm audit fix
```

**Create security checklist** (`docs/security-checklist.md`):

```markdown
# Security Checklist

## Authentication & Authorization
- [x] Firebase Auth integration working
- [x] JWT tokens validated on every request
- [x] tenant_id filtering on all database queries
- [x] No endpoints accessible without authentication
- [x] Admin endpoints require admin role

## Data Protection
- [x] All PII encrypted at rest (GCS encryption, Cloud SQL encryption)
- [x] All connections use TLS (HTTPS only)
- [x] Database credentials in Secret Manager
- [x] API keys not committed to git
- [x] Signed URLs for document access (expire in 1 hour)

## Input Validation
- [x] All inputs validated with Pydantic schemas
- [x] File upload size limits enforced (50 MB)
- [x] File type validation (PDF, JPG, PNG only)
- [x] SQL injection prevented (using ORM)
- [x] XSS prevented (React escaping, CSP headers)

## Rate Limiting
- [x] API rate limits implemented (Redis-based)
- [x] Upload rate limits per user
- [x] Chat message rate limits

## Security Headers
- [x] HSTS enabled
- [x] CSP configured
- [x] X-Frame-Options: DENY
- [x] X-Content-Type-Options: nosniff

## Logging & Monitoring
- [x] All authentication events logged
- [x] Failed login attempts monitored
- [x] Data access audit trail
- [x] Security alerts configured

## Compliance (GDPR)
- [x] Data retention policies defined
- [x] Right to deletion implemented
- [x] Data export capability
- [x] Privacy policy displayed

## Infrastructure
- [x] Cloud Run services not publicly accessible (except API Gateway)
- [x] VPC connector for database access
- [x] IAM roles follow least privilege
- [x] Service accounts for each service
```

**Run penetration tests**:

```bash
# Install OWASP ZAP for automated security testing
# Manual test cases:

# 1. Test authentication bypass
curl -X GET https://api-gateway-xxx.run.app/documents \
  -H "Authorization: Bearer invalid_token"
# Should return 401

# 2. Test tenant isolation
# Login as user A, try to access user B's documents
# Should return 404

# 3. Test SQL injection
curl -X GET "https://api-gateway-xxx.run.app/documents?status='; DROP TABLE documents; --"
# Should return 422 validation error

# 4. Test file upload limits
# Try uploading 100 MB file
# Should return 413

# 5. Test XSS in document names
# Upload file with name: <script>alert('xss')</script>.pdf
# Should be sanitized

# 6. Test rate limiting
for i in {1..20}; do
  curl -X POST https://api-gateway-xxx.run.app/documents/upload
done
# Should return 429 after limit exceeded
```

### Verification

```bash
# Security scan results
bandit -r backend/
# Target: 0 high severity issues

safety check
# Target: 0 known vulnerabilities

# Frontend audit
npm audit
# Target: 0 high/critical vulnerabilities

# Security headers check
curl -I https://api-gateway-xxx.run.app/health
# Verify all security headers present

# Penetration test
# Complete manual test cases checklist
# Document any findings and fix immediately
```

---

## Task 7.5: Documentation (8 hours)

### Objective
Create comprehensive documentation for users, developers, and operators.

### Subtasks

#### 7.5.1: User Documentation (3 hours)

**Create user guide** (`docs/user-guide.md`):

```markdown
# Document AI SaaS - User Guide

## Getting Started

### 1. Sign Up

Visit [https://your-app.vercel.app](https://your-app.vercel.app) and click "Sign Up".

Enter your:
- Email address
- Password (minimum 8 characters)
- Company name

You'll receive a verification email. Click the link to activate your account.

### 2. Upload Your First Document

1. Click "Upload Document" in the sidebar
2. Select document type:
   - **Invoice**: For invoices, receipts, purchase orders
   - **Contract**: For contracts and agreements
   - **ID Card**: For Romanian ID cards, passports
   - **Generic**: For any other document
3. Click "Choose File" and select a PDF, JPG, or PNG (max 50 MB)
4. Click "Upload and Process"

Processing takes 10-30 seconds depending on document type.

## Features

### Invoice Processing

**What it does**: Extracts key data from invoices automatically.

**How to use**:
1. Upload invoice (PDF or image)
2. Wait for processing (15-20 seconds)
3. Review extracted data:
   - Supplier name
   - Invoice number
   - Date
   - Line items
   - Total amount
4. Click "Edit" to correct any errors
5. Click "Approve" to finalize
6. Export to JSON or CSV

**Tips**:
- Ensure invoice is clear and readable
- Best results with digital PDFs
- Scanned invoices work too (may be less accurate)

### Generic OCR

**What it does**: Extracts all text from any document.

**How to use**:
1. Upload document
2. Select "Generic OCR"
3. Choose OCR method:
   - **Auto**: We choose the best method (recommended)
   - **Standard**: Fast, good for clear documents
   - **Advanced**: Slower, better for poor quality
4. Wait for processing (10-60 seconds)
5. Copy or download extracted text

**Tips**:
- Use "Advanced" for handwritten or low-quality scans
- Text layout may not be preserved perfectly
- For tables, consider using spreadsheet export

### Document Summarization

**What it does**: Creates concise summaries of long documents.

**How to use**:
1. Upload document (works best with multi-page PDFs)
2. Select "Summarize"
3. Choose options:
   - **Length**: Concise (1 paragraph) or Detailed (multiple paragraphs)
   - **Model**: Flash (faster) or Pro (higher quality)
4. Wait for processing (20-40 seconds)
5. Review summary and key points
6. Copy or download

**Tips**:
- Best for documents over 2 pages
- Use "Pro" model for complex documents
- Summaries are in English (even if document is Romanian)

### Chat with PDF

**What it does**: Ask questions about your document in natural language.

**How to use**:
1. Upload document
2. Click "Chat" tab
3. Type your question (e.g., "What is the total contract value?")
4. Get instant answer with source citations
5. Continue conversation with follow-up questions

**Example questions**:
- "Summarize the main terms of this contract"
- "What are the payment terms?"
- "Who are the parties involved?"
- "What is the delivery date?"

**Tips**:
- Be specific in your questions
- System shows which page the answer came from
- Works best with structured documents

### Document Filling (Romanian IDs)

**What it does**: Automatically fills PDF forms using data from Romanian ID cards.

**How to use**:
1. Upload Romanian ID card (buletin) photo
2. Select "Document Filling"
3. Choose PDF template to fill (e.g., "Cerere tip")
4. System extracts: Name, CNP, Birth date, Address
5. Review pre-filled data
6. Click "Generate PDF"
7. Download filled form

**Tips**:
- Ensure ID card photo is clear and well-lit
- All 4 corners should be visible
- Review extracted data before generating PDF

## Account Management

### Usage Limits (Free Tier)

- 50 documents per month
- 500 chat messages per month
- Document storage: 30 days

### Upgrade to Pro

For higher limits:
- Visit Settings > Billing
- Choose a plan
- Enter payment details

### Data Export

To export all your data:
1. Go to Settings > Data & Privacy
2. Click "Export My Data"
3. Download ZIP file with all documents and extracted data

### Delete Account

To delete your account:
1. Go to Settings > Data & Privacy
2. Click "Delete Account"
3. Confirm deletion
4. All your data will be permanently deleted within 7 days

## Troubleshooting

### Processing Failed

**Possible causes**:
- Document quality too poor
- File corrupted
- Unsupported format

**Solutions**:
- Try higher quality scan
- Re-save PDF
- Convert to PDF if image

### Slow Processing

**Possible causes**:
- Large file size
- Complex document
- High server load

**Solutions**:
- Compress PDF before upload
- Try during off-peak hours
- Contact support if persistent

### Incorrect Data Extraction

**For invoices**:
- Use "Edit" feature to correct
- Send feedback to improve our system

**For OCR**:
- Try "Advanced" OCR method
- Improve document quality

## Support

- Email: support@documentai.com
- Live chat: Available in app (Mon-Fri 9 AM - 5 PM CET)
- Help center: https://help.documentai.com
```

#### 7.5.2: API Documentation (2 hours)

**Generate OpenAPI docs automatically** (`backend/api_gateway/main.py`):

```python
app = FastAPI(
    title="Document AI SaaS API",
    description="Intelligent document processing API with OCR, summarization, and chat capabilities",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI at /docs
    redoc_url="/redoc", # ReDoc at /redoc
    openapi_tags=[
        {"name": "authentication", "description": "Authentication endpoints"},
        {"name": "documents", "description": "Document management"},
        {"name": "invoice", "description": "Invoice processing"},
        {"name": "ocr", "description": "OCR operations"},
        {"name": "summarization", "description": "Document summarization"},
        {"name": "chat", "description": "Chat with PDF"},
        {"name": "filling", "description": "Document filling"},
    ]
)

# Example endpoint with full documentation
@router.post(
    "/documents/upload",
    tags=["documents"],
    summary="Upload a document for processing",
    description="""
    Upload a document file (PDF, JPG, or PNG) for processing.

    The document will be stored in Google Cloud Storage and a processing job
    will be created based on the specified document type.

    **Supported document types:**
    - `invoice`: Invoice or receipt processing
    - `contract`: Contract analysis
    - `id_card`: Romanian ID card extraction
    - `generic`: Generic OCR

    **File requirements:**
    - Maximum size: 50 MB
    - Formats: PDF, JPG, PNG
    - Must be readable (not corrupted)

    **Rate limits:** 10 uploads per minute per user
    """,
    response_model=DocumentResponse,
    responses={
        200: {
            "description": "Document uploaded successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "doc_abc123",
                        "filename": "invoice.pdf",
                        "status": "processing",
                        "created_at": "2025-11-17T10:30:00Z"
                    }
                }
            }
        },
        413: {"description": "File too large"},
        422: {"description": "Invalid file type or document type"},
        429: {"description": "Rate limit exceeded"}
    }
)
async def upload_document(...):
    pass
```

**Access API docs**:
- Swagger UI: `https://api-gateway-xxx.run.app/docs`
- ReDoc: `https://api-gateway-xxx.run.app/redoc`
- OpenAPI JSON: `https://api-gateway-xxx.run.app/openapi.json`

#### 7.5.3: Deployment Documentation (2 hours)

**Create deployment guide** (`docs/deployment-guide.md`):

```markdown
# Deployment Guide

## Prerequisites

- Google Cloud Platform account with billing enabled
- gcloud CLI installed and authenticated
- Terraform installed (v1.5+)
- Docker installed
- Firebase project created

## Initial Setup

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/document-ai-saas.git
cd document-ai-saas
```

### 2. Set Environment Variables

```bash
export PROJECT_ID="your-gcp-project-id"
export REGION="europe-west1"
export FIREBASE_PROJECT="your-firebase-project"
```

### 3. Enable GCP APIs

```bash
./scripts/setup-gcp.sh
```

This enables:
- Cloud Run
- Cloud SQL
- Cloud Storage
- Pub/Sub
- Document AI
- Vertex AI
- Secret Manager

### 4. Initialize Terraform

```bash
cd terraform
terraform init
terraform plan -var="project_id=$PROJECT_ID"
terraform apply -var="project_id=$PROJECT_ID"
```

This creates:
- Cloud SQL database
- Cloud Storage buckets
- Pub/Sub topics and subscriptions
- Service accounts
- IAM roles

### 5. Database Setup

```bash
# Run migrations
cd backend
alembic upgrade head
```

### 6. Build and Deploy Services

```bash
# Build all Docker images
./scripts/build-all.sh

# Deploy all services
./scripts/deploy-all.sh
```

### 7. Deploy Frontend

```bash
cd frontend
npm install
npm run build

# Deploy to Vercel
vercel --prod
```

### 8. Verify Deployment

```bash
# Check all services are running
./scripts/health-check.sh
```

## Updating

### Backend Updates

```bash
# Make changes to code
# Build and deploy specific service
./scripts/deploy-service.sh api-gateway

# Or deploy all
./scripts/deploy-all.sh
```

### Frontend Updates

```bash
cd frontend
npm run build
vercel --prod
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head
```

## Monitoring

- **Logs**: https://console.cloud.google.com/logs
- **Monitoring**: https://console.cloud.google.com/monitoring
- **Cloud Run**: https://console.cloud.google.com/run

## Rollback

### Rollback Cloud Run Service

```bash
# List revisions
gcloud run revisions list --service=api-gateway --region=$REGION

# Rollback to previous revision
gcloud run services update-traffic api-gateway \
  --to-revisions=api-gateway-00002-xyz=100 \
  --region=$REGION
```

### Rollback Database

```bash
# Downgrade one version
alembic downgrade -1

# Downgrade to specific version
alembic downgrade <revision_id>
```

## Troubleshooting

### Service Not Starting

```bash
# Check logs
gcloud run services logs read api-gateway --region=$REGION --limit=100

# Check service status
gcloud run services describe api-gateway --region=$REGION
```

### Database Connection Issues

```bash
# Test connection from Cloud Shell
gcloud sql connect documentai-db --user=postgres

# Check Cloud SQL Proxy
gcloud sql instances describe documentai-db
```

### Environment Variables

```bash
# List secrets
gcloud secrets list

# Check service environment
gcloud run services describe api-gateway --region=$REGION --format="value(spec.template.spec.containers[0].env)"
```
```

#### 7.5.4: Admin Guide (1 hour)

**Create admin operations guide** (`docs/admin-guide.md`):

```markdown
# Administrator Guide

## Daily Operations

### Monitor System Health

```bash
# Check all services status
gcloud run services list --region=europe-west1

# Check error rates
gcloud logging read "severity=ERROR" --limit=50 --format=json

# Check queue depths
gcloud pubsub subscriptions list
```

### Review Metrics

1. Open Cloud Console Monitoring Dashboard
2. Check:
   - Request rate
   - Error rate
   - Response latency
   - Queue depths
   - Database connections

### Respond to Alerts

**High Error Rate Alert**:
1. Check logs for error patterns
2. Identify affected service
3. Check recent deployments
4. Rollback if necessary

**API Down Alert**:
1. Check service status
2. Check database connectivity
3. Check external dependencies (Firebase, Document AI)
4. Restart service if needed

## User Management

### View User Activity

```sql
-- Connect to database
gcloud sql connect documentai-db --user=postgres

-- Top users by document count
SELECT tenant_id, COUNT(*) as doc_count
FROM documents
GROUP BY tenant_id
ORDER BY doc_count DESC
LIMIT 20;

-- Recent uploads
SELECT tenant_id, filename, created_at
FROM documents
ORDER BY created_at DESC
LIMIT 50;
```

### Delete User Data (GDPR)

```bash
# Use admin script
python scripts/delete_user_data.py --tenant-id=<tenant_id> --confirm
```

## Performance Optimization

### Scale Services

```bash
# Increase max instances
gcloud run services update api-gateway \
  --max-instances=20 \
  --region=europe-west1
```

### Optimize Database

```sql
-- Check slow queries
SELECT query, calls, mean_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Analyze tables
ANALYZE documents;
VACUUM ANALYZE documents;
```

## Backup and Recovery

### Manual Backup

```bash
# Backup database
gcloud sql backups create --instance=documentai-db

# List backups
gcloud sql backups list --instance=documentai-db
```

### Restore from Backup

```bash
# Restore to point in time
gcloud sql backups restore <BACKUP_ID> \
  --backup-instance=documentai-db \
  --backup-id=<BACKUP_ID>
```

### Backup Documents

```bash
# Sync GCS bucket to local
gsutil -m rsync -r gs://your-bucket-documents ./backup/
```

## Cost Management

### Review Costs

```bash
# View current month costs
gcloud billing accounts list
gcloud billing budgets list
```

### Optimize Costs

1. **Reduce Cloud Run idle time**: Set min instances to 0 for workers
2. **Optimize database**: Use smallest instance that meets performance
3. **Clean old documents**: Delete documents older than retention period
4. **Use Gemini Flash**: Set as default over Pro model

## Security Tasks

### Rotate Secrets

```bash
# Update database password
gcloud sql users set-password postgres \
  --instance=documentai-db \
  --password=<NEW_PASSWORD>

# Update Secret Manager
gcloud secrets versions add database-password \
  --data-file=new-password.txt
```

### Review IAM Permissions

```bash
# List service accounts
gcloud iam service-accounts list

# Review permissions
gcloud projects get-iam-policy $PROJECT_ID
```

### Security Scan

```bash
# Run security scan
python scripts/security_scan.py

# Review results
cat security-report.json
```
```

### Verification

```bash
# Verify all documentation files created
ls docs/
# Should see:
# - user-guide.md
# - deployment-guide.md
# - admin-guide.md

# Test API docs accessible
curl https://api-gateway-xxx.run.app/docs
curl https://api-gateway-xxx.run.app/openapi.json

# Review documentation with team
# Get feedback from at least one beta user
```

---

## Task 7.6: Beta Launch Execution (8 hours)

### Objective
Successfully onboard initial beta users and collect feedback.

### Subtasks

#### 7.6.1: Beta User Onboarding (3 hours)

**Create onboarding email template** (`docs/beta-onboarding-email.md`):

```markdown
Subject: Welcome to Document AI SaaS Beta! 🚀

Hi [Name],

Thank you for joining our beta program! We're excited to have you test our intelligent document processing platform.

## Your Access Details

- **App URL**: https://your-app.vercel.app
- **Sign up** with your email: [email]
- **Support email**: beta-support@documentai.com

## What to Test

We'd love your feedback on these 5 key features:

1. **Invoice Processing**: Upload an invoice, review extracted data
2. **Generic OCR**: Extract text from any document
3. **Document Summarization**: Get AI summaries of long documents
4. **Chat with PDF**: Ask questions about your documents
5. **Document Filling** (Romanian IDs): Auto-fill forms from ID cards

## Getting Started

1. Sign up at the app URL above
2. Upload your first document (we recommend starting with an invoice)
3. Explore the different AI features
4. Share your feedback!

## What We Need from You

**During beta (2 weeks):**

- ✅ Test all 5 features with real documents
- ✅ Complete short feedback survey (5 min) after first use
- ✅ Report any bugs or issues you encounter
- ✅ Join our feedback call (30 min, optional)

**Feedback Survey**: [Google Forms Link]

## Beta Perks

As a beta user, you get:
- **Free access** during beta (2 weeks)
- **50% discount** on first 3 months after launch
- **Priority support** during beta
- **Influence** on product roadmap

## Known Limitations

Please note:
- Processing may be slower during peak times
- Some edge cases may not work perfectly
- UI may have minor glitches

## Support

Need help?
- Email: beta-support@documentai.com
- Slack: [Beta Users Channel]
- Response time: < 4 hours (Mon-Fri, 9 AM - 5 PM CET)

Looking forward to your feedback!

Best regards,
[Your Name]
Document AI Team
```

**Create beta user tracking spreadsheet**:

| Email | Signup Date | Last Login | Documents Uploaded | Features Used | Feedback Submitted | Issues Reported | NPS Score |
|-------|-------------|------------|-------------------|---------------|-------------------|-----------------|-----------|
| user1@example.com | 2025-11-17 | 2025-11-18 | 12 | Invoice, OCR, Chat | Yes | 2 | 9 |
| user2@example.com | 2025-11-17 | 2025-11-17 | 3 | Invoice | No | 0 | - |

**Send onboarding emails**:

```bash
# Use script to send personalized emails
python scripts/send_beta_invitations.py \
  --emails beta-users.csv \
  --template docs/beta-onboarding-email.md
```

#### 7.6.2: Feedback Collection System (2 hours)

**Create feedback survey** (Google Forms):

**Part 1: User Profile**
1. What industry do you work in?
   - Legal
   - Logistics
   - Finance
   - Healthcare
   - Other: ___

2. How many documents do you process per week?
   - < 10
   - 10-50
   - 50-200
   - 200+

**Part 2: Feature Feedback**

For each feature (Invoice Processing, OCR, Summarization, Chat, Filling):

3. Did you try [Feature]?
   - Yes
   - No (why not?)

4. How easy was [Feature] to use? (1-5)

5. How accurate were the results? (1-5)

6. What would make [Feature] more useful?

**Part 3: Overall**

7. What feature did you find most valuable?

8. What feature needs the most improvement?

9. Would you pay for this product?
   - Definitely yes
   - Probably yes
   - Not sure
   - Probably not
   - Definitely not

10. How likely are you to recommend this to a colleague? (NPS 0-10)

11. Any other feedback or suggestions?

**Create in-app feedback widget** (`frontend/src/components/common/FeedbackWidget.tsx`):

```typescript
import { useState } from 'react';
import { api } from '../../services/api';

export const FeedbackWidget: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [feedback, setFeedback] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async () => {
    try {
      await api.post('/feedback', {
        message: feedback,
        page: window.location.pathname,
        timestamp: new Date().toISOString()
      });
      setSubmitted(true);
      setTimeout(() => {
        setIsOpen(false);
        setSubmitted(false);
        setFeedback('');
      }, 2000);
    } catch (error) {
      console.error('Failed to submit feedback:', error);
    }
  };

  return (
    <>
      {/* Floating feedback button */}
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-4 right-4 bg-blue-600 text-white px-4 py-2 rounded-full shadow-lg hover:bg-blue-700 transition-colors"
      >
        💬 Beta Feedback
      </button>

      {/* Feedback modal */}
      {isOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            {submitted ? (
              <div className="text-center py-8">
                <div className="text-4xl mb-4">✅</div>
                <h3 className="text-xl font-semibold mb-2">Thank you!</h3>
                <p className="text-gray-600">Your feedback helps us improve.</p>
              </div>
            ) : (
              <>
                <h3 className="text-xl font-semibold mb-4">Beta Feedback</h3>
                <p className="text-sm text-gray-600 mb-4">
                  Help us improve! Share your thoughts, report bugs, or suggest features.
                </p>
                <textarea
                  value={feedback}
                  onChange={(e) => setFeedback(e.target.value)}
                  placeholder="What's on your mind?"
                  className="w-full border border-gray-300 rounded-lg p-3 mb-4 h-32 resize-none"
                />
                <div className="flex gap-2">
                  <button
                    onClick={() => setIsOpen(false)}
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSubmit}
                    disabled={!feedback.trim()}
                    className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
                  >
                    Submit
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </>
  );
};
```

**Add feedback API endpoint** (`backend/api_gateway/routes/feedback.py`):

```python
from fastapi import APIRouter, Depends
from backend.shared.schemas import FeedbackSubmission
from backend.shared.auth import get_current_user
from backend.shared.logging import api_logger

router = APIRouter(prefix="/feedback", tags=["feedback"])

@router.post("/")
async def submit_feedback(
    feedback: FeedbackSubmission,
    current_user: dict = Depends(get_current_user)
):
    """Submit beta feedback"""

    # Log feedback
    api_logger.info(
        "Beta feedback received",
        user_id=current_user["user_id"],
        tenant_id=current_user["tenant_id"],
        page=feedback.page,
        message=feedback.message
    )

    # In production, also save to database and/or send to Slack
    # For beta, logging is sufficient for immediate review

    return {"status": "success", "message": "Thank you for your feedback!"}
```

#### 7.6.3: Monitor Beta Usage (2 hours)

**Create beta analytics dashboard** (`scripts/beta_analytics.py`):

```python
#!/usr/bin/env python3
"""
Generate beta analytics report
"""
from sqlalchemy import func, create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import pandas as pd

def generate_beta_report():
    """Generate comprehensive beta usage report"""

    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()

    # Date range
    beta_start = datetime(2025, 11, 17)
    beta_end = datetime(2025, 12, 1)

    print("=" * 60)
    print("BETA ANALYTICS REPORT")
    print(f"Period: {beta_start.date()} to {beta_end.date()}")
    print("=" * 60)

    # 1. User Signup and Activation
    total_signups = db.query(func.count(Tenant.id)).filter(
        Tenant.created_at >= beta_start,
        Tenant.created_at <= beta_end
    ).scalar()

    active_users = db.query(func.count(func.distinct(Document.tenant_id))).filter(
        Document.created_at >= beta_start,
        Document.created_at <= beta_end
    ).scalar()

    print(f"\n📊 USER METRICS")
    print(f"Total Signups: {total_signups}")
    print(f"Active Users (uploaded ≥1 doc): {active_users}")
    print(f"Activation Rate: {active_users/total_signups*100:.1f}%")

    # 2. Document Processing
    doc_stats = db.query(
        Document.document_type,
        func.count(Document.id).label('count')
    ).filter(
        Document.created_at >= beta_start,
        Document.created_at <= beta_end
    ).group_by(Document.document_type).all()

    print(f"\n📄 DOCUMENTS PROCESSED")
    for doc_type, count in doc_stats:
        print(f"{doc_type}: {count}")

    # 3. Feature Usage
    feature_usage = db.query(
        ProcessingJob.job_type,
        func.count(ProcessingJob.id).label('count'),
        func.avg(func.extract('epoch', ProcessingJob.completed_at - ProcessingJob.created_at)).label('avg_duration')
    ).filter(
        ProcessingJob.created_at >= beta_start,
        ProcessingJob.created_at <= beta_end,
        ProcessingJob.status == 'completed'
    ).group_by(ProcessingJob.job_type).all()

    print(f"\n🎯 FEATURE USAGE")
    for job_type, count, avg_duration in feature_usage:
        print(f"{job_type}: {count} jobs (avg {avg_duration:.1f}s)")

    # 4. Error Analysis
    error_rate = db.query(
        ProcessingJob.job_type,
        func.count(ProcessingJob.id).label('total'),
        func.sum(case((ProcessingJob.status == 'failed', 1), else_=0)).label('failed')
    ).filter(
        ProcessingJob.created_at >= beta_start,
        ProcessingJob.created_at <= beta_end
    ).group_by(ProcessingJob.job_type).all()

    print(f"\n⚠️  ERROR RATES")
    for job_type, total, failed in error_rate:
        rate = failed/total*100 if total > 0 else 0
        print(f"{job_type}: {failed}/{total} ({rate:.1f}%)")

    # 5. Chat Usage
    chat_stats = db.query(
        func.count(ChatMessage.id).label('total_messages'),
        func.count(func.distinct(ChatMessage.session_id)).label('sessions'),
        func.avg(func.char_length(ChatMessage.content)).label('avg_message_length')
    ).filter(
        ChatMessage.created_at >= beta_start,
        ChatMessage.created_at <= beta_end
    ).first()

    print(f"\n💬 CHAT METRICS")
    print(f"Total Messages: {chat_stats.total_messages}")
    print(f"Chat Sessions: {chat_stats.sessions}")
    print(f"Avg Message Length: {chat_stats.avg_message_length:.0f} chars")

    # 6. Daily Active Users
    dau = db.query(
        func.date(Document.created_at).label('date'),
        func.count(func.distinct(Document.tenant_id)).label('users')
    ).filter(
        Document.created_at >= beta_start,
        Document.created_at <= beta_end
    ).group_by(func.date(Document.created_at)).all()

    print(f"\n📈 DAILY ACTIVE USERS")
    for date, users in dau:
        print(f"{date}: {users} users")

    db.close()

    print("\n" + "=" * 60)

if __name__ == "__main__":
    generate_beta_report()
```

**Run daily during beta**:

```bash
# Add to cron or Cloud Scheduler
0 9 * * * cd /app && python scripts/beta_analytics.py | mail -s "Daily Beta Report" team@documentai.com
```

#### 7.6.4: Iterate Based on Feedback (1 hour)

**Create feedback review process**:

1. **Daily** (15 min):
   - Review new in-app feedback submissions
   - Check error logs for common issues
   - Respond to urgent support requests

2. **Every 3 days** (1 hour):
   - Analyze usage metrics
   - Review survey responses
   - Prioritize bug fixes
   - Create GitHub issues for top requests

3. **Weekly** (2 hours):
   - Beta team sync meeting
   - Demo improvements to beta users
   - Plan next iteration

**Bug triage template** (GitHub Issues):

```markdown
## Bug Report from Beta User

**Reporter**: [User email/ID]
**Date**: 2025-11-19
**Feature**: Invoice Processing
**Severity**: Medium

### Description
Invoice extraction failed for PDF with rotated pages.

### Steps to Reproduce
1. Upload invoice PDF with 90° rotated pages
2. Wait for processing
3. Extraction returns empty data

### Expected Behavior
Should detect rotation and extract correctly

### Actual Behavior
Returns empty invoice_data

### Impact
Affects 2 beta users, ~5% of invoices

### Fix Priority
- [ ] Critical (blocking beta)
- [x] High (should fix this week)
- [ ] Medium (fix before launch)
- [ ] Low (nice to have)

### Proposed Solution
Add rotation detection to Document AI preprocessing
```

### Verification

```bash
# Beta launch checklist
echo "Beta Launch Verification"

# 1. All beta users invited
echo "✅ Beta invitation emails sent: 10/10"

# 2. All users activated
python scripts/check_beta_activation.py
# Target: 80%+ activation rate

# 3. All features tested
echo "✅ Invoice Processing: 8/10 users"
echo "✅ Generic OCR: 6/10 users"
echo "✅ Summarization: 7/10 users"
echo "✅ Chat: 5/10 users"
echo "✅ Filling: 3/10 users (Romanian ID specific)"

# 4. Feedback collected
echo "✅ Survey responses: 7/10"
echo "✅ In-app feedback: 23 submissions"
echo "✅ NPS Score: 8.2/10"

# 5. Critical bugs fixed
echo "✅ P0 bugs: 0 open"
echo "✅ P1 bugs: 2 open (in progress)"

# 6. Daily analytics running
echo "✅ Analytics script running daily"
```

---

## Phase 7 Completion Checklist

### Task 7.1: Frontend Polish ✅
- [ ] Loading states and skeletons implemented
- [ ] Comprehensive error handling
- [ ] Responsive design for mobile/tablet/desktop
- [ ] Accessibility improvements (ARIA labels, keyboard nav)
- [ ] Lighthouse score 90+ (performance, accessibility)

### Task 7.2: Monitoring ✅
- [ ] Structured logging with Cloud Logging
- [ ] Cloud Monitoring dashboards created
- [ ] Alert policies configured
- [ ] Sentry integrated for frontend errors
- [ ] Custom metrics for worker processing times

### Task 7.3: Performance ✅
- [ ] Database indexes created and analyzed
- [ ] Redis caching implemented
- [ ] Cloud Run configurations optimized
- [ ] Frontend bundle size < 500 KB
- [ ] API response time < 200ms (p95)

### Task 7.4: Security ✅
- [ ] Security headers configured
- [ ] Input validation strengthened
- [ ] Rate limiting implemented
- [ ] Security audit completed
- [ ] 0 high-severity vulnerabilities

### Task 7.5: Documentation ✅
- [ ] User guide published
- [ ] API documentation auto-generated
- [ ] Deployment guide created
- [ ] Admin operations guide created

### Task 7.6: Beta Launch ✅
- [ ] 10 beta users onboarded
- [ ] 80%+ activation rate
- [ ] Feedback survey responses collected
- [ ] NPS score ≥ 7
- [ ] All P0 bugs fixed
- [ ] Daily analytics running

---

## Success Criteria

**Phase 7 is complete when:**

1. ✅ **Production Ready**: All services deployed, monitored, and stable
2. ✅ **Secure**: Security audit passed, no critical vulnerabilities
3. ✅ **Performant**: < 200ms API response time, 90+ Lighthouse score
4. ✅ **Documented**: Complete user, API, deployment, and admin docs
5. ✅ **Beta Validated**: ≥8 active beta users, NPS ≥7, < 5% error rate
6. ✅ **Feedback Loop**: Daily metrics, weekly iterations based on feedback

**Deliverables:**
- Polished, production-ready application
- Comprehensive monitoring and alerting
- Complete documentation suite
- Beta user validation and feedback
- Go/no-go decision for public launch

**Next Steps After Phase 7:**
- Review beta feedback and metrics
- Decide: Public launch or iterate
- If launching: Prepare marketing materials, pricing page, onboarding flow
- If iterating: Prioritize top 3 beta requests, implement, re-test

---

## Estimated Timeline

- **Week 11**: Tasks 7.1, 7.2, 7.3 (polish, monitoring, performance)
- **Week 12**: Tasks 7.4, 7.5, 7.6 (security, docs, beta launch)

**Total**: ~80 hours over 2 weeks

---

## Notes

- Phase 7 is critical - this determines launch readiness
- Don't skip security or monitoring - required for production
- Beta feedback drives post-launch roadmap
- Be prepared to iterate 2-3 times based on beta feedback before public launch
- Document all beta learnings for future reference
