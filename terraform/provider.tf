provider "google" {
  project = var.project_id
  region  = var.region
}

terraform {
  required_version = ">= 1.0"
  backend "gcs" {
    # Bucket name will be provided via -backend-config during init
    # bucket = "kintai-sync-tfstate-[PROJECT_ID]"
    prefix = "terraform/state"
  }
}
