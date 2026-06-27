# 1. Artifact Registry
resource "google_artifact_registry_repository" "repo" {
  location      = var.region
  repository_id = "${var.app_prefix}-repo"
  description   = "Docker repository for Kintai Sync services"
  format        = "DOCKER"
  
  # Ensure images are deleted when repo is destroyed
  cleanup_policies {
    id     = "delete-old-images"
    action = "DELETE"
    condition {
      tag_state = "ANY"
    }
  }
}

# 2. Add force_destroy to all potential stateful resources
# (Already set for google_storage_bucket.screenshots and google_firestore_database.database)

# 3. Secret Manager with immediate deletion
# We define them here so terraform can destroy them.
# Note: Values are entered manually in Console, but the container (Secret) is managed here.
resource "google_secret_manager_secret" "slack_bot_token" {
  secret_id = "${var.app_prefix}-slack-bot-token"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "slack_signing_secret" {
  secret_id = "${var.app_prefix}-slack-signing-secret"
  replication {
    auto {}
  }
}
