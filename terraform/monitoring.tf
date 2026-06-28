# 1. Notification Channel (Email)
resource "google_monitoring_notification_channel" "email" {
  display_name = "Kintai Sync Admin"
  type         = "email"
  labels = {
    email_address = var.admin_email
  }
}

# 2. Alert Policy for Worker Failures (Critical Errors in Logs)
resource "google_monitoring_alert_policy" "worker_error" {
  display_name = "Kintai Sync Worker Error"
  combiner     = "OR"
  conditions {
    display_name = "Error log detected"
    condition_matched_log {
      filter = "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${var.app_prefix}-worker\" AND severity>=ERROR"
    }
  }

  notification_channels = [google_monitoring_notification_channel.email.name]

  alert_strategy {
    notification_rate_limit {
      period = "3600s" # Notify at most once per hour
    }
  }
}
