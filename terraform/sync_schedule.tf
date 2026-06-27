# 1. Cloud Run for Settings Sync
resource "google_cloud_run_v2_service" "sync" {
  name     = "${var.app_prefix}-sync"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_INTERNAL_ONLY"

  template {
    service_account = google_service_account.sync_sa.email
    containers {
      image = "asia-northeast1-docker.pkg.dev/${var.project_id}/${var.app_prefix}-repo/sync:latest"
      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      env {
        name  = "SETTINGS_SPREADSHEET_ID"
        value = "placeholder-id" # Should be a variable
      }
    }
  }
}

# 2. Cloud Scheduler Trigger
resource "google_cloud_scheduler_job" "sync_job" {
  name             = "${var.app_prefix}-sync-job"
  description      = "Sync settings from Google Sheets to Firestore"
  schedule         = "0 * * * *" # Every hour
  time_zone        = "Asia/Tokyo"
  attempt_deadline = "320s"

  retry_config {
    retry_count = 1
  }

  http_target {
    http_method = "POST"
    uri         = "${google_cloud_run_v2_service.sync.uri}/sync" # Note: sync.py needs a web endpoint if called via HTTP
    
    oidc_token {
      service_account_email = google_service_account.sync_sa.email
    }
  }
}

# 3. Allow Scheduler to call Sync Service
resource "google_cloud_run_v2_service_iam_member" "sync_invoker" {
  location = google_cloud_run_v2_service.sync.location
  name     = google_cloud_run_v2_service.sync.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.sync_sa.email}"
}
