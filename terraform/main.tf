# 1. APIs to Enable
resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com",
    "cloudtasks.googleapis.com",
    "firestore.googleapis.com",
    "secretmanager.googleapis.com",
    "aiplatform.googleapis.com",
    "sheets.googleapis.com",
    "calendar-json.googleapis.com"
  ])
  service            = each.key
  disable_on_destroy = false
}

# 2. Service Accounts
resource "google_service_account" "receiver_sa" {
  account_id   = "${var.app_prefix}-receiver-sa"
  display_name = "SA for Kintai Sync Receiver"
}

resource "google_service_account" "worker_sa" {
  account_id   = "${var.app_prefix}-worker-sa"
  display_name = "SA for Kintai Sync Worker"
}

# 3. Firestore (Default Database)
resource "google_firestore_database" "database" {
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"

  # Ensure it doesn't get deleted easily if data is precious, 
  # but here we follow user's destroy request.
  deletion_policy = "DELETE"
}

# 4. Cloud Tasks Queue
resource "google_cloud_tasks_queue" "queue" {
  name     = "${var.app_prefix}-queue"
  location = var.region

  rate_limits {
    max_dispatches_per_second = 1
    max_concurrent_dispatches = 5
  }

  retry_config {
    max_attempts  = 5
    max_backoff   = "3600s"
    min_backoff   = "10s"
    max_doublings = 5
  }
}

# 5. GCS Bucket for Screenshots
resource "google_storage_bucket" "screenshots" {
  name          = "${var.app_prefix}-screenshots-${var.project_id}"
  location      = var.region
  force_destroy = true # As requested for clean destroy

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }
}
