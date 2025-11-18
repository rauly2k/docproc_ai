output "connection_name" {
  description = "Cloud SQL connection name"
  value       = google_sql_database_instance.main.connection_name
  sensitive   = true
}

output "database_url" {
  description = "PostgreSQL connection string"
  value       = "postgresql://${google_sql_user.main.name}:${random_password.db_password.result}@${google_sql_database_instance.main.public_ip_address}:5432/${google_sql_database.main.name}"
  sensitive   = true
}

output "instance_name" {
  description = "Cloud SQL instance name"
  value       = google_sql_database_instance.main.name
}

output "public_ip_address" {
  description = "Public IP address"
  value       = google_sql_database_instance.main.public_ip_address
  sensitive   = true
}

output "private_ip_address" {
  description = "Private IP address"
  value       = google_sql_database_instance.main.private_ip_address
  sensitive   = true
}

output "database_name" {
  description = "Database name"
  value       = google_sql_database.main.name
}
