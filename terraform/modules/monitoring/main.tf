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
          title = "API Gateway - Error Rate"
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
        }
      ]
    }
  })
}

# Uptime Check for API Gateway
resource "google_monitoring_uptime_check_config" "api_gateway" {
  count = var.enable_uptime_checks ? 1 : 0

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
      host       = var.api_gateway_url
    }
  }
}
