variable "gcp_project" {
  description = "The GCP team project id"
}

variable "kube_namespace" {
  description = "The Kubernetes namespace"
}

variable "load_config_file" {
  description = "Do not load kube config file"
  default     = false
}

variable "labels" {
  description = "Labels used in all resources"
  type        = map(string)
  default = {
    manager = "terraform"
    team    = "ror"
    slack   = "talk-ror"
    app     = "otp-travelsearch-qa"
  }
}

variable "reports_bucket_name" {
  description = "Name of bucket for report uploads"
}

variable "reports_bucket_role" {
  description = "Role needed on bucket for report uploads"
  default = "roles/storage.objectAdmin"
}
