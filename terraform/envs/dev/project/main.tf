terraform {
  required_providers {
    random = {
      source  = "hashicorp/random"
      version = "3.4.3"
    }
    google = {
      source  = "hashicorp/google"
      version = "4.49.0"
    }
  }
}

provider "random" {
  # Configuration options
}

resource "random_string" "random" {
  length  = 8
  special = false
  lower   = true
  upper   = false
}

module "dev_project" {
  source = "../../../modules/project"

  project_name    = var.project_name
  project_id      = local.project_id
  org_id          = var.org_id
  billing_account = var.billing_account

  tf_remote_storage_buckets = local.tf_remote_storage_buckets
}
