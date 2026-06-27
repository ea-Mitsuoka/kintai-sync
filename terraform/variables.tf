variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region for resources"
  type        = string
  default     = "asia-northeast1"
}

variable "app_prefix" {
  description = "Prefix for all resources"
  type        = string
  default     = "kintai-sync"
}

variable "settings_spreadsheet_id" {
  description = "The ID of the Google Spreadsheet for user settings"
  type        = string
  default     = ""
}
