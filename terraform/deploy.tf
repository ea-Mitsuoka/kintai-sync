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

resource "google_project_iam_member" "worker_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.worker_sa.email}"
}

resource "google_project_iam_member" "worker_ai_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.worker_sa.email}"
}

resource "google_project_iam_member" "worker_gcs_creator" {
  project = var.project_id
  role    = "roles/storage.objectCreator"
  member  = "serviceAccount:${google_service_account.worker_sa.email}"
}

# 3. IAM Roles for Sync SA
resource "google_project_iam_member" "sync_firestore_user" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.sync_sa.email}"
}

# 4. Cloud Run Services (Basic Definition)
# Note: Containers must be pushed to Artifact Registry first.
# These resources are placeholders for the full deployment logic.

resource "google_cloud_run_v2_service" "receiver" {
  name     = "${var.app_prefix}-receiver"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.receiver_sa.email
    containers {
      image = "asia-northeast1-docker.pkg.dev/${var.project_id}/${var.app_prefix}-repo/receiver:latest"
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
  ingress  = "INGRESS_TRAFFIC_INTERNAL_ONLY" # Only triggered by Tasks

  template {
    service_account = google_service_account.worker_sa.email
    containers {
      image = "asia-northeast1-docker.pkg.dev/${var.project_id}/${var.app_prefix}-repo/worker:latest"
      resources {
        limits = {
          cpu    = "2"
          memory = "2Gi"
        }
      }
    }
  }
}
