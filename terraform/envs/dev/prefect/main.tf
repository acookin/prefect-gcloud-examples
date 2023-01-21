terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "4.49.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "2.16.1"
    }
  }
  backend "gcs" {
    bucket = "dev-project-tfstate-801f1993e9b2f506"
    prefix = "state/dev/prefect/"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

module "prefect" {
  source = "../../../modules/prefect"

  cluster_name               = var.cluster_name
  region                     = var.region
  project_id                 = var.project_id
  prefect_cloud_account_id   = var.prefect_cloud_account_id
  prefect_cloud_workspace_id = var.prefect_cloud_workspace_id
  prefect_api_key            = var.prefect_api_key
}
