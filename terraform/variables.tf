variable "project_id" {
  description = "The GCP project ID"
  type        = str
}

variable "region" {
  description = "The GCP region for resources"
  type        = str
  default     = "asia-northeast1"
}

variable "app_prefix" {
  description = "Prefix for all resources"
  type        = str
  default     = "kintai-sync"
}
