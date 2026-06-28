# 1. IAM Roles for Receiver SA
resource "google_project_iam_member" "receiver_tasks_enqueuer" {
  project = var.project_id
  role    = "roles/cloudtasks.enqueuer"
  member  = "serviceAccount:${google_service_account.receiver_sa.email}"
}

# 2. IAM Roles for Worker SA
resource "google_project_iam_member" "worker_firestore_user" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.worker_sa.email}"
}

# 3. IAM Roles for Worker SA (Secret Accessor)
resource "google_project_iam_member" "worker_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.worker_sa.email}"
}

# 4. IAM Roles for Worker SA (AI Platform User)
resource "google_project_iam_member" "worker_ai_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.worker_sa.email}"
}

# 5. IAM Roles for Worker SA (Storage Creator)
resource "google_project_iam_member" "worker_gcs_creator" {
  project = var.project_id
  role    = "roles/storage.objectCreator"
  member  = "serviceAccount:${google_service_account.worker_sa.email}"
}

# 6. Cloud Run Services (Basic Definition)
resource "google_cloud_run_v2_service" "receiver" {
  name     = "${var.app_prefix}-receiver"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.receiver_sa.email
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${var.app_prefix}-repo/receiver:latest"
      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      env {
        name  = "WORKER_URL"
        value = google_cloud_run_v2_service.worker.uri
      }
    }
  }
}

resource "google_cloud_run_v2_service" "worker" {
  name     = "${var.app_prefix}-worker"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_INTERNAL_ONLY"

  template {
    service_account = google_service_account.worker_sa.email
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${var.app_prefix}-repo/worker:latest"
      resources {
        limits = {
          cpu    = "2"
          memory = "2Gi"
        }
      }
      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      # The Worker reads user settings directly from the spreadsheet on a
      # lazy read-through basis (see src/sync.py). No separate sync service.
      env {
        name  = "SETTINGS_SPREADSHEET_ID"
        value = var.settings_spreadsheet_id
      }
    }
  }
}

# 7. Public Access (Receiver Only)
resource "google_cloud_run_v2_service_iam_member" "receiver_public" {
  location = google_cloud_run_v2_service.receiver.location
  name     = google_cloud_run_v2_service.receiver.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# 8. Internal Invocation (Receiver calls Worker)
resource "google_cloud_run_v2_service_iam_member" "receiver_invokes_worker" {
  location = google_cloud_run_v2_service.worker.location
  name     = google_cloud_run_v2_service.worker.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.receiver_sa.email}"
}
