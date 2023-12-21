# Contains main description of bulk of terraform?
terraform {
  required_version = ">= 0.13.2"
}

provider "google" {
  version = "~> 4.84.0"
}

provider "kubernetes" {
  version = ">= 2.13.1"
}

resource "google_storage_bucket" "reports_bucket" {
  name          = "otp-travelsearch-qa-reports-${var.env_suffix}"
  location      = "EUROPE-WEST1"
  project = var.gcp_project

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
  member = "serviceAccount:${var.default_sa}"
}
