output "dashboard_id" {
  description = "ID of the monitoring dashboard"
  value       = google_monitoring_dashboard.main.id
}

output "notification_channel_id" {
  description = "ID of the email notification channel"
  value       = length(google_monitoring_notification_channel.email) > 0 ? google_monitoring_notification_channel.email[0].id : null
}
