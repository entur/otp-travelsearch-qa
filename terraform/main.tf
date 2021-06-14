
terraform {
  required_version = ">= 0.13.2"
}

provider "google" {
  version = "~> 2.19"
}

provider "kubernetes" {
  version = "~> 1.13.3"
  load_config_file = var.load_config_file
}

resource "google_service_account" "service_account" {
  account_id   = "${var.labels.team}-${var.labels.app}-sa"
  display_name = "${var.labels.team}-${var.labels.app} service account"
  project = var.gcp_project
}

resource "google_service_account_key" "service_account_key" {
  service_account_id = google_service_account.service_account.name
}

resource "kubernetes_secret" "service_account_credentials" {
  metadata {
    name      = "${var.labels.team}-${var.labels.app}-sa-key"
    namespace = var.kube_namespace
  }
  data = {
    "credentials.json" = base64decode(google_service_account_key.service_account_key.private_key)
  }
}

resource "google_storage_bucket" "reports_bucket" {
  name          = "otp-travelsearch-qa-reports-${var.kube_namespace}"
  location      = "EU"

  cors {
    origin          = ["*"]
    method          = ["GET"]
    response_header = ["*"]
    max_age_seconds = 3600
  }

  lifecycle_rule {

    condition {
      age = 30
    }

    action {
      type = "Delete"
    }
  }
}

resource "google_storage_bucket_iam_member" "reports_bucket_iam" {
  bucket = google_storage_bucket.reports_bucket.name
  role = var.reports_bucket_role
  member = "serviceAccount:${google_service_account.service_account.email}"
}
