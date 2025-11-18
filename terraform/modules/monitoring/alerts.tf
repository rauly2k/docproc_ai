# High Error Rate Alert
resource "google_monitoring_alert_policy" "high_error_rate" {
  count = var.enable_alerts ? 1 : 0

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

  notification_channels = var.notification_channels

  alert_strategy {
    auto_close = "1800s"
  }

  documentation {
    content   = "Error rate has exceeded 5% for the last 5 minutes. Check logs for details."
    mime_type = "text/markdown"
  }
}

# API Downtime Alert
resource "google_monitoring_alert_policy" "api_down" {
  count = var.enable_alerts && var.enable_uptime_checks ? 1 : 0

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

  notification_channels = var.notification_channels

  alert_strategy {
    auto_close = "1800s"
  }

  documentation {
    content   = "API Gateway uptime check has failed. Service may be down."
    mime_type = "text/markdown"
  }
}

# High Latency Alert
resource "google_monitoring_alert_policy" "high_latency" {
  count = var.enable_alerts ? 1 : 0

  display_name = "High API Latency"
  combiner     = "OR"

  conditions {
    display_name = "P95 latency > 1000ms"

    condition_threshold {
      filter          = "resource.type=\"cloud_run_revision\" AND metric.type=\"run.googleapis.com/request_latencies\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 1000

      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_DELTA"
        cross_series_reducer = "REDUCE_PERCENTILE_95"
        group_by_fields      = ["resource.service_name"]
      }
    }
  }

  notification_channels = var.notification_channels

  alert_strategy {
    auto_close = "1800s"
  }

  documentation {
    content   = "API response time P95 has exceeded 1000ms for 5 minutes."
    mime_type = "text/markdown"
  }
}

# Database Connection Pool Exhaustion
resource "google_monitoring_alert_policy" "db_connections_high" {
  count = var.enable_alerts ? 1 : 0

  display_name = "Database Connection Pool High"
  combiner     = "OR"

  conditions {
    display_name = "Active connections > 80% of max"

    condition_threshold {
      filter          = "resource.type=\"cloudsql_database\" AND metric.type=\"cloudsql.googleapis.com/database/postgresql/num_backends\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 80

      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }

  notification_channels = var.notification_channels

  alert_strategy {
    auto_close = "1800s"
  }

  documentation {
    content   = "Database connection pool is near capacity. Consider scaling or investigating connection leaks."
    mime_type = "text/markdown"
  }
}

# Notification Channel (Email)
resource "google_monitoring_notification_channel" "email" {
  count = var.alert_email != "" ? 1 : 0

  display_name = "Email Notification"
  type         = "email"

  labels = {
    email_address = var.alert_email
  }
}
