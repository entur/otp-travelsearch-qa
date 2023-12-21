variable "gcp_project" {
  description = "The GCP team project id"
}

variable "labels" {
  description = "Labels used in all resources"
  type        = map(string)
  default = {
    manager = "terraform"
    team    = "ror"
    slack   = "talk-ror"
    app     = "otptrvlqa"
  }
}

variable "reports_bucket_role" {
  description = "Role needed on bucket for report uploads"
  default = "roles/storage.admin"
}

variable "env_suffix" {}

variable "default_sa" {}