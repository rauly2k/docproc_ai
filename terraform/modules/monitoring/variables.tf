variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "europe-west1"
}

variable "api_gateway_url" {
  description = "URL of the API Gateway for uptime checks"
  type        = string
  default     = ""
}

variable "enable_uptime_checks" {
  description = "Enable uptime checks"
  type        = bool
  default     = true
}

variable "enable_alerts" {
  description = "Enable alert policies"
  type        = bool
  default     = true
}

variable "alert_email" {
  description = "Email address for alerts"
  type        = string
  default     = ""
}

variable "notification_channels" {
  description = "List of notification channel IDs"
  type        = list(string)
  default     = []
}
